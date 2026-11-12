"""把 ``.memgraph`` 的泄漏报告符号化到源码行。

设备返回的图里已经带符号名 (设备侧用目标自身的符号表解析), 所以
``leaks`` 能直接打印 ``ViewController.leakRawBuffer(bytes:)`` 这样的帧;
但 ``file:line`` 只有 macOS 在 Spotlight 里找到同 UUID 的 dSYM 时才会打印。
本模块用 ``atos`` + 调用方给出的 dSYM 补上源码位置, 不依赖 Spotlight。
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

from .exceptions import LeaksError

#: 报告头部的主程序加载地址 (ASLR slide 后的地址)。
LOAD_ADDRESS_RE = re.compile(r"^Load Address:\s+(0x[0-9a-fA-F]+)\s*$", re.MULTILINE)
CODE_TYPE_RE = re.compile(r"^Code Type:\s+(\S+)", re.MULTILINE)
#: 调用栈帧: "3   LeakDemo   0x100248f8c  ViewController.leakRawBuffer(bytes:) + 44"
FRAME_RE = re.compile(r"^\s*(?P<index>\d+)\s+(?P<image>\S+)\s+(?P<address>0x[0-9a-fA-F]+)\s+(?P<symbol>.*)$")
#: atos 输出末尾的 "(/path/File.swift:42)"
SOURCE_RE = re.compile(r"\(([^()]+:\d+)\)$")

ARCH_BY_CODE_TYPE = {"ARM64": "arm64", "ARM64E": "arm64e", "X86_64": "x86_64"}
ATOS_BATCH_SIZE = 500

#: 已符号化的帧: 地址 -> "file:line"
SourceMap = Dict[str, str]


def _dwarf_file(dsym: Union[str, Path]) -> Path:
    """接受 dSYM 目录、DWARF 文件或 .app 路径, 返回真正的 DWARF 文件。"""
    path = Path(dsym)
    if path.name.endswith(".app"):
        path = path.with_name(path.name + ".dSYM")
    if path.is_dir():
        dwarf_dir = path / "Contents" / "Resources" / "DWARF"
        if not dwarf_dir.is_dir():
            raise LeaksError(f"not a dSYM bundle (missing Contents/Resources/DWARF): {path}")
        candidates = [entry for entry in dwarf_dir.iterdir() if entry.is_file()]
        if not candidates:
            raise LeaksError(f"dSYM bundle has no DWARF file: {path}")
        return candidates[0]
    if not path.is_file():
        raise LeaksError(f"dSYM not found: {path}")
    return path


def _arch_from_report(report: str) -> str:
    match = CODE_TYPE_RE.search(report)
    if match is None:
        return "arm64"
    return ARCH_BY_CODE_TYPE.get(match.group(1).upper(), "arm64")


def _atos(dwarf: Path, arch: str, load_address: str, addresses: List[str]) -> List[str]:
    resolved: List[str] = []
    for start in range(0, len(addresses), ATOS_BATCH_SIZE):
        batch = addresses[start : start + ATOS_BATCH_SIZE]
        result = subprocess.run(
            ["atos", "-o", str(dwarf), "-arch", arch, "-l", load_address, *batch],
            capture_output=True,
            text=True,
            errors="replace",
        )
        if result.returncode != 0:
            raise LeaksError(f"atos failed: {result.stderr.strip() or result.returncode}")
        resolved.extend(result.stdout.splitlines())
    return resolved


def annotate_report(report: str, dsym: Union[str, Path]) -> str:
    """给 ``leaks`` 报告里的调用栈帧追加 ``<-- file:line``。

    只注解能在给定 dSYM 里解析出源码位置的帧; 其他帧保持原样。
    """
    load = LOAD_ADDRESS_RE.search(report)
    if load is None:
        return report

    lines = report.splitlines()
    frame_positions: List[int] = []
    frame_addresses: List[str] = []
    for index, line in enumerate(lines):
        match = FRAME_RE.match(line)
        if match is not None:
            frame_positions.append(index)
            frame_addresses.append(match.group("address"))
    if not frame_addresses:
        return report

    resolved = _atos(_dwarf_file(dsym), _arch_from_report(report), load.group(1), frame_addresses)
    sources: SourceMap = {}
    for address, symbol in zip(frame_addresses, resolved):
        match = SOURCE_RE.search(symbol)
        if match is not None:
            sources[address] = match.group(1)

    for index in frame_positions:
        address = FRAME_RE.match(lines[index]).group("address")
        source = sources.get(address)
        if source is not None:
            lines[index] = f"{lines[index]}   <-- {source}"
    return "\n".join(lines) + ("\n" if report.endswith("\n") else "")


def leaks_available() -> bool:
    """当前主机是否能运行 macOS 的 ``leaks``。"""
    return sys.platform == "darwin" and shutil.which("leaks") is not None


def analyze_memgraph(graph: Union[str, Path], dsym: Optional[Union[str, Path]] = None) -> str:
    """在本机运行 ``leaks`` 读取 ``.memgraph``, 可选地注解源码行。

    :raises LeaksError: 不在 macOS / 没有 leaks(1) / 文件读取失败
    """
    if not leaks_available():
        raise LeaksError("analyzing a .memgraph needs macOS's leaks(1) tool")

    result = subprocess.run(
        [shutil.which("leaks") or "leaks", str(graph)],
        capture_output=True,
        text=True,
        errors="replace",
    )
    report = result.stdout or result.stderr
    if not report.strip():
        raise LeaksError(f"leaks produced no output for {graph}: {result.stderr.strip()}")
    if dsym is not None:
        report = annotate_report(report, dsym)
    return report

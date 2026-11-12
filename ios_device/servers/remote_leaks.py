"""Leaks 通道: 抓取进程内存图并读取泄漏地址。

服务 ``com.apple.instruments.server.services.remoteleaks`` 与 Instruments 的
Leaks 模板同源: 设备通过目标进程的 task port 扫描堆, 因此目标必须可调试
(开发签名 / ``get-task-allow``) 且已经在运行 —— 挂起在启动阶段的进程还没有堆。

返回的内存图是 macOS ``leaks(1)`` / ``heap(1)`` / ``vmmap(1)`` 可直接读取的
``.memgraph`` 格式。
"""

import dataclasses
from pathlib import Path
from typing import Any, List, Optional, Union

from ..util.dtx_msg import RawInt64sl
from ..util.exceptions import LeaksError
from ..util.variables import InstrumentsService
from .dvt import REPLY_TIMEOUT

#: 完整内存图 + 泄漏数量 + 泄漏地址。
#: 注意 ``LeakedGraphOnly=True`` 时设备不会再返回 ``LeakedAddresses``。
DEFAULT_OPTIONS = {"LeakedCount": True, "LeakedAddresses": True, "LeakedGraphOnly": False}


@dataclasses.dataclass
class MemoryGraph:
    """一次 Leaks 扫描的结果。"""

    pid: int
    leaked_count: int
    #: 泄漏块的运行时地址 (带 ASLR slide), 需要配合 dSYM 符号化。
    leaked_addresses: List[int]
    #: ``.memgraph`` 内容; 泄漏数为 0 时设备不返回图。
    data: Optional[bytes] = None

    @property
    def has_graph(self) -> bool:
        return bool(self.data)

    def save(self, path: Union[str, Path]) -> Path:
        """把内存图写到本地文件, 返回实际路径。"""
        if not self.data:
            raise LeaksError("no memory graph was returned (the process has no leaks)")
        path = Path(path)
        path.write_bytes(self.data)
        return path


def parse_memory_graph_response(payload: Any, pid: int) -> MemoryGraph:
    """解析 ``requestGraph:options:`` 的返回值。

    正常应答是 NSDictionary; 失败时设备回 NSError, bpylist2 会把它解码成
    带 ``$class='NSError'`` 的 dict。
    """
    if not isinstance(payload, dict):
        raise LeaksError(f"pid {pid}: unexpected leaks response: {payload!r}")

    if payload.get("$class") == "NSError":
        user_info = payload.get("userinfo") or {}
        reason = user_info.get("NSLocalizedDescription") or payload.get("domain") or payload
        raise LeaksError(f"pid {pid}: {reason}")

    raw_graph = payload.get("SerializedGraph")
    if raw_graph is not None and not isinstance(raw_graph, (bytes, bytearray, memoryview)):
        raise LeaksError(f"pid {pid}: SerializedGraph is {type(raw_graph).__name__}, expected bytes")

    if raw_graph is None and "LeakedCount" not in payload:
        raise LeaksError(f"pid {pid}: leaks response has neither SerializedGraph nor LeakedCount")

    try:
        count = int(payload.get("LeakedCount") or 0)
        addresses = [int(address) for address in payload.get("LeakedAddresses") or []]
    except (TypeError, ValueError) as e:
        raise LeaksError(f"pid {pid}: malformed leaks response: {e}") from e

    return MemoryGraph(
        pid=pid,
        leaked_count=count,
        leaked_addresses=addresses,
        data=bytes(raw_graph) if raw_graph is not None else None,
    )


class RemoteLeaks:
    """基于已有 InstrumentServer 的 Leaks 通道。"""

    SERVICE = InstrumentsService.RemoteLeaks

    def __init__(self, rpc):
        self.rpc = rpc

    def memory_graph(self, pid: int, leaked_only: bool = False, timeout: float = REPLY_TIMEOUT) -> MemoryGraph:
        """抓取 ``pid`` 的内存图。

        :param pid: 目标进程, 必须是已经运行的进程。
        :param leaked_only: 只保留泄漏节点, 图更小, 但设备不会返回泄漏地址。
        :param timeout: 等待设备生成/传输内存图的秒数, 大 App 需要调大。
        :raises LeaksError: 设备无法检查该进程 (例如非调试签名) 或应答损坏。
        """
        options = dict(DEFAULT_OPTIONS, LeakedGraphOnly=bool(leaked_only))
        response = self.rpc.call(
            self.SERVICE,
            "requestGraph:options:",
            # pid 必须按 64 位整数发送: 设备会把 32 位值当成上一次图的 token。
            RawInt64sl(int(pid)),
            options,
            timeout=timeout,
        )
        return parse_memory_graph_response(response.selector if response is not None else None, int(pid))

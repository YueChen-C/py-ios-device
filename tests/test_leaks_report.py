"""Unit tests for :mod:`ios_device.util.leaks_report` (no device required)."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ios_device.util import leaks_report
from ios_device.util.exceptions import LeaksError

SAMPLE_REPORT = """Hardware Model:  iPhone12,8
Process:         LeakDemo [1]
Load Address:    0x100000000
Code Type:       ARM64

STACK OF 1 INSTANCE OF 'ROOT LEAK: <malloc in ViewController.leakRawBuffer(bytes:)>':
3  LeakDemo                 0x100000abc ViewController.leakRawBuffer(bytes:) + 44
2  libsystem_malloc.dylib   0x1dfa97ecc _malloc_zone_malloc + 204
    1 (64.0K) ROOT LEAK: <malloc in ViewController.leakRawBuffer(bytes:) 0x105ed0000> [65536]
"""


def make_dsym(root: Path, name: str = "LeakDemo") -> Path:
    dsym = root / f"{name}.app.dSYM"
    dwarf_dir = dsym / "Contents" / "Resources" / "DWARF"
    dwarf_dir.mkdir(parents=True)
    (dwarf_dir / name).write_bytes(b"dwarf")
    return dsym


class TestDwarfFile(unittest.TestCase):
    def test_dsym_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsym = make_dsym(Path(tmp))
            self.assertEqual(leaks_report._dwarf_file(dsym).name, "LeakDemo")

    def test_app_path_maps_to_sibling_dsym(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_dsym(Path(tmp))
            self.assertEqual(leaks_report._dwarf_file(Path(tmp) / "LeakDemo.app").name, "LeakDemo")

    def test_plain_dwarf_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            dwarf = Path(tmp) / "LeakDemo"
            dwarf.write_bytes(b"dwarf")
            self.assertEqual(leaks_report._dwarf_file(dwarf), dwarf)

    def test_missing_path(self):
        with self.assertRaises(LeaksError):
            leaks_report._dwarf_file("/nonexistent/LeakDemo.app.dSYM")


class TestAnnotateReport(unittest.TestCase):
    def test_adds_source_lines_and_keeps_unresolved_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsym = make_dsym(Path(tmp))
            resolved = [
                "ViewController.leakRawBuffer(bytes:) (in LeakDemo) (ViewController.swift:49)",
                "_malloc_zone_malloc + 204",
            ]
            with mock.patch.object(leaks_report, "_atos", return_value=resolved) as atos:
                annotated = leaks_report.annotate_report(SAMPLE_REPORT, dsym)

            self.assertIn("ViewController.leakRawBuffer(bytes:) + 44   <-- ViewController.swift:49", annotated)
            self.assertIn("_malloc_zone_malloc + 204\n", annotated)
            _, arch, load, addresses = atos.call_args[0]
            self.assertEqual(arch, "arm64")
            self.assertEqual(load, "0x100000000")
            self.assertEqual(addresses, ["0x100000abc", "0x1dfa97ecc"])

    def test_arch_is_taken_from_code_type(self):
        report = SAMPLE_REPORT.replace("ARM64", "ARM64E")
        with tempfile.TemporaryDirectory() as tmp:
            dsym = make_dsym(Path(tmp))
            with mock.patch.object(leaks_report, "_atos", return_value=["??", "??"]) as atos:
                leaks_report.annotate_report(report, dsym)
            self.assertEqual(atos.call_args[0][1], "arm64e")

    def test_report_without_load_address_is_returned_unchanged(self):
        report = SAMPLE_REPORT.replace("Load Address:    0x100000000\n", "")
        self.assertEqual(leaks_report.annotate_report(report, "/nonexistent"), report)

    def test_report_without_frames_is_returned_unchanged(self):
        report = "Load Address:    0x100000000\nCode Type:       ARM64\n"
        self.assertEqual(leaks_report.annotate_report(report, "/nonexistent"), report)

    def test_trailing_newline_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsym = make_dsym(Path(tmp))
            with mock.patch.object(leaks_report, "_atos", return_value=["??", "??"]):
                annotated = leaks_report.annotate_report(SAMPLE_REPORT, dsym)
            self.assertTrue(annotated.endswith("\n"))

    def test_atos_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            dsym = make_dsym(Path(tmp))
            failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="bad dSYM")
            with mock.patch.object(leaks_report.subprocess, "run", return_value=failed):
                with self.assertRaises(LeaksError) as raised:
                    leaks_report.annotate_report(SAMPLE_REPORT, dsym)
            self.assertIn("bad dSYM", str(raised.exception))


class TestAnalyzeMemgraph(unittest.TestCase):
    def test_requires_macos_leaks(self):
        with mock.patch.object(leaks_report, "leaks_available", return_value=False):
            with self.assertRaises(LeaksError):
                leaks_report.analyze_memgraph("/tmp/app.memgraph")

    def test_returns_leaks_output(self):
        completed = subprocess.CompletedProcess(args=[], returncode=1, stdout="leak report", stderr="")
        with mock.patch.object(leaks_report, "leaks_available", return_value=True), mock.patch.object(
            leaks_report.shutil, "which", return_value="/usr/bin/leaks"
        ), mock.patch.object(leaks_report.subprocess, "run", return_value=completed):
            self.assertEqual(leaks_report.analyze_memgraph("/tmp/app.memgraph"), "leak report")

    def test_annotates_when_dsym_is_given(self):
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="report", stderr="")
        with mock.patch.object(leaks_report, "leaks_available", return_value=True), mock.patch.object(
            leaks_report.shutil, "which", return_value="/usr/bin/leaks"
        ), mock.patch.object(leaks_report.subprocess, "run", return_value=completed), mock.patch.object(
            leaks_report, "annotate_report", return_value="annotated"
        ) as annotate:
            self.assertEqual(leaks_report.analyze_memgraph("/tmp/app.memgraph", "/tmp/App.app.dSYM"), "annotated")
            annotate.assert_called_once_with("report", "/tmp/App.app.dSYM")

    def test_empty_output_is_reported(self):
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        with mock.patch.object(leaks_report, "leaks_available", return_value=True), mock.patch.object(
            leaks_report.shutil, "which", return_value="/usr/bin/leaks"
        ), mock.patch.object(leaks_report.subprocess, "run", return_value=completed):
            with self.assertRaises(LeaksError):
                leaks_report.analyze_memgraph("/tmp/app.memgraph")


if __name__ == "__main__":
    unittest.main()

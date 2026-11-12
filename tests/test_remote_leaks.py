"""Unit tests for :mod:`ios_device.servers.remote_leaks` (no device required)."""

import tempfile
import unittest
from pathlib import Path

from ios_device.servers.remote_leaks import MemoryGraph, RemoteLeaks, parse_memory_graph_response
from ios_device.util.dtx_msg import RawInt64sl
from ios_device.util.exceptions import LeaksError
from ios_device.util.variables import InstrumentsService


class FakeResponse:
    def __init__(self, selector):
        self.selector = selector


class FakeRPC:
    """记录 call 参数并返回预设 selector，不碰设备。"""

    def __init__(self, selector):
        self.selector = selector
        self.calls = []

    def call(self, channel, selector, *auxiliaries, **kwargs):
        self.calls.append((channel, selector, auxiliaries, kwargs))
        return FakeResponse(self.selector)


class TestParseMemoryGraphResponse(unittest.TestCase):
    def test_full_graph(self):
        graph = parse_memory_graph_response(
            {"SerializedGraph": b"\x01\x02", "LeakedCount": 3, "LeakedAddresses": [0x1000, 0x2000]},
            pid=42,
        )
        self.assertEqual(graph.pid, 42)
        self.assertEqual(graph.leaked_count, 3)
        self.assertEqual(graph.leaked_addresses, [0x1000, 0x2000])
        self.assertEqual(graph.data, b"\x01\x02")
        self.assertTrue(graph.has_graph)

    def test_clean_process_has_no_graph(self):
        graph = parse_memory_graph_response({"LeakedCount": 0, "LeakedAddresses": []}, pid=42)
        self.assertEqual(graph.leaked_count, 0)
        self.assertEqual(graph.leaked_addresses, [])
        self.assertIsNone(graph.data)
        self.assertFalse(graph.has_graph)

    def test_leaked_only_keeps_count_but_no_addresses(self):
        graph = parse_memory_graph_response({"LeakedCount": 7, "LeakedAddresses": []}, pid=42)
        self.assertEqual(graph.leaked_count, 7)
        self.assertEqual(graph.leaked_addresses, [])
        self.assertFalse(graph.has_graph)

    def test_memoryview_graph_is_converted_to_bytes(self):
        graph = parse_memory_graph_response(
            {"SerializedGraph": memoryview(b"abc"), "LeakedCount": 1, "LeakedAddresses": [1]},
            pid=42,
        )
        self.assertEqual(graph.data, b"abc")
        self.assertIsInstance(graph.data, bytes)

    def test_ns_error_carries_device_reason(self):
        payload = {
            "$class": "NSError",
            "domain": "DTLeaksService",
            "code": -1,
            "userinfo": {"NSLocalizedDescription": "Unable to acquire required task port (42:0)"},
        }
        with self.assertRaises(LeaksError) as raised:
            parse_memory_graph_response(payload, pid=42)
        self.assertIn("task port", str(raised.exception))

    def test_unexpected_payload(self):
        for payload in (None, "oops", b"\x00"):
            with self.subTest(payload=payload), self.assertRaises(LeaksError):
                parse_memory_graph_response(payload, pid=42)

    def test_missing_graph_and_count(self):
        with self.assertRaises(LeaksError):
            parse_memory_graph_response({}, pid=42)

    def test_bad_graph_type(self):
        with self.assertRaises(LeaksError) as raised:
            parse_memory_graph_response({"SerializedGraph": "not-bytes", "LeakedCount": 1}, pid=42)
        self.assertIn("expected bytes", str(raised.exception))

    def test_bad_addresses(self):
        with self.assertRaises(LeaksError):
            parse_memory_graph_response({"LeakedCount": 1, "LeakedAddresses": ["x"]}, pid=42)


class TestRemoteLeaks(unittest.TestCase):
    def test_request_uses_int64_pid_and_asks_for_addresses(self):
        rpc = FakeRPC({"LeakedCount": 0, "LeakedAddresses": []})
        pid = 0x7FFFFFFF + 5  # 超出 int32，必须按 int64 发送
        RemoteLeaks(rpc).memory_graph(pid)

        channel, selector, auxiliaries, _ = rpc.calls[0]
        self.assertEqual(channel, InstrumentsService.RemoteLeaks)
        self.assertEqual(selector, "requestGraph:options:")
        pid_arg, options = auxiliaries
        self.assertIsInstance(pid_arg, RawInt64sl)
        self.assertEqual(pid_arg.data, (pid,))
        self.assertTrue(options["LeakedCount"])
        self.assertTrue(options["LeakedAddresses"])
        self.assertFalse(options["LeakedGraphOnly"])

    def test_leaked_only_sets_graph_option(self):
        rpc = FakeRPC({"LeakedCount": 1, "LeakedAddresses": []})
        RemoteLeaks(rpc).memory_graph(42, leaked_only=True)
        _, _, auxiliaries, _ = rpc.calls[0]
        self.assertTrue(auxiliaries[1]["LeakedGraphOnly"])

    def test_timeout_is_forwarded(self):
        rpc = FakeRPC({"LeakedCount": 0, "LeakedAddresses": []})
        RemoteLeaks(rpc).memory_graph(42, timeout=5.5)
        self.assertEqual(rpc.calls[0][3]["timeout"], 5.5)

    def test_none_response_is_reported(self):
        with self.assertRaises(LeaksError):
            RemoteLeaks(FakeRPC(None)).memory_graph(42)


class TestMemoryGraphSave(unittest.TestCase):
    def test_save_writes_graph(self):
        graph = MemoryGraph(pid=1, leaked_count=1, leaked_addresses=[0x1000], data=b"graph")
        with tempfile.TemporaryDirectory() as tmp:
            path = graph.save(Path(tmp) / "app.memgraph")
            self.assertEqual(path.read_bytes(), b"graph")

    def test_save_without_graph_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(LeaksError):
                MemoryGraph(pid=1, leaked_count=0, leaked_addresses=[]).save(Path(tmp) / "app.memgraph")


if __name__ == "__main__":
    unittest.main()

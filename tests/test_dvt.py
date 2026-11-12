"""DTXClient/DTXServer 单元测试 (ios_device.servers.dvt)。

用假 socket 模拟字节流, 覆盖分片重组、消息分发与应答超时, 不需要真机。
"""

import queue
import unittest
from collections import defaultdict
from unittest import mock

from ios_device.servers.dvt import DTXClient, DTXEnum, DTXServer
from ios_device.util.dtx_msg import DTXMessage, MessageAux, dtx_message_header, object_to_aux
from ios_device.util.exceptions import InstrumentRPCParseError, MuxError


class FakeSocket:
    """把预置字节按任意粒度吐给 recv, 模拟真实 socket 的分片到达。"""

    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.sent = []
        self.closed = False

    def recv(self, n):
        if not self.chunks:
            return b""
        chunk = self.chunks[0][:n]
        self.chunks[0] = self.chunks[0][len(chunk) :]
        if not self.chunks[0]:
            self.chunks.pop(0)
        return chunk

    def send(self, data):
        self.sent.append(bytes(data))
        return len(data)

    def close(self):
        self.closed = True


def message_bytes(msg: DTXMessage) -> bytes:
    return bytes(msg)


def make_fragment_header(fragment_id, fragment_count, payload_length, channel=0, identifier=1, conversation_index=0):
    return dtx_message_header.build(
        {
            "header_length": dtx_message_header.sizeof(),
            "fragment_id": fragment_id,
            "fragment_count": fragment_count,
            "payload_length": payload_length,
            "identifier": identifier,
            "conversation_index": conversation_index,
            "channel": channel,
            "expects_reply": 0,
        }
    )


def make_message(
    selector="sel:", aux_values=(), channel=0, identifier=1, conversation_index=0, expects_reply=0
) -> bytes:
    aux = MessageAux()
    for v in aux_values:
        object_to_aux(v, aux)
    msg = DTXMessage(
        selector,
        channel_code=channel,
        identifier=identifier,
        conversation_index=conversation_index,
        expects_reply=expects_reply,
        auxiliaries=aux,
    )
    return bytes(msg)


class TestDTXClientRecv(unittest.TestCase):
    def test_single_fragment_message(self):
        data = make_message("runningProcesses", aux_values=[42])
        sock = FakeSocket([data])
        dtx = DTXClient().recv_dtx(sock)
        self.assertEqual("runningProcesses", dtx.selector)
        self.assertEqual([42], dtx.auxiliaries)

    def test_recv_satisfies_exact_length_across_chunks(self):
        """recv 需要跨多个到达分片凑满指定长度。"""
        data = make_message("sel")
        sock = FakeSocket([data[i : i + 3] for i in range(0, len(data), 3)])
        dtx = DTXClient().recv_dtx(sock)
        self.assertEqual("sel", dtx.selector)

    def test_multi_fragment_message_is_reassembled(self):
        """三片消息: 首片只有头部 (payload_length 为总长), 后两片各带一段载荷。"""
        full = make_message("multiFrag", aux_values=[1, 2], identifier=5)
        payload = full[dtx_message_header.sizeof() :]
        frag0 = make_fragment_header(0, 3, len(payload), identifier=5)
        frag1 = make_fragment_header(1, 3, len(payload[:5]), identifier=5) + payload[:5]
        frag2 = make_fragment_header(2, 3, len(payload[5:]), identifier=5) + payload[5:]
        sock = FakeSocket([frag0, frag1, frag2])
        dtx = DTXClient().recv_dtx(sock)
        self.assertEqual("multiFrag", dtx.selector)
        self.assertEqual([1, 2], dtx.auxiliaries)
        self.assertEqual(5, dtx.identifier)

    def test_fragment_without_first_header_is_dropped(self):
        """缺少首片头部的分片被跳过, 不影响后续消息。"""
        good = make_message("good", identifier=7)
        orphan = make_fragment_header(1, 2, 4) + b"xxxx"
        sock = FakeSocket([orphan, good])
        dtx = DTXClient().recv_dtx(sock)
        self.assertEqual("good", dtx.selector)

    def test_connection_closed_raises_mux_error(self):
        sock = FakeSocket([])
        with self.assertRaises(MuxError):
            DTXClient().recv_dtx(sock)

    def test_channels_are_reassembled_independently(self):
        """两个 channel 的分片交错到达, 各自完整重组。"""
        a = make_message("chanA", channel=1, identifier=10)
        b = make_message("chanB", channel=2, identifier=11)
        pa, pb = a[dtx_message_header.sizeof() :], b[dtx_message_header.sizeof() :]
        stream = [
            make_fragment_header(0, 2, len(pa), channel=1),
            make_fragment_header(0, 2, len(pb), channel=2),
            make_fragment_header(1, 2, len(pa), channel=1) + pa,
            make_fragment_header(1, 2, len(pb), channel=2) + pb,
        ]
        sock = FakeSocket(stream)
        dtx = DTXClient().recv_dtx(sock)
        self.assertEqual("chanA", dtx.selector)  # channel 1 的末片先到达
        self.assertEqual(1, dtx.channel_code)

    def test_send_dtx(self):
        sock = FakeSocket([])
        msg = DTXMessage("ping", channel_code=1, identifier=1)
        n = DTXClient().send_dtx(sock, msg)
        self.assertEqual(len(bytes(msg)), n)
        self.assertEqual([bytes(msg)], sock.sent)


class TestDTXServerDispatch(unittest.TestCase):
    """_dispatch 路由规则: 应答队列 / 通道回调 / selector 回调 / 兜底。"""

    def setUp(self):
        self.server = DTXServer.__new__(DTXServer)  # 跳过 __init__ 的能力协商注册
        self.server._cli = None
        self.server._callbacks = {}
        self.server._undefined_callback = None
        self.server._channel_callbacks = {}
        self.server._reply_queues = defaultdict(queue.Queue)
        self.server._client = mock.Mock()

    def _msg(self, **kw):
        return DTXMessage.decode(*self._msg_raw(**kw))

    @staticmethod
    def _msg_raw(selector="sel", aux_values=(), channel=0, identifier=1, conversation_index=0, expects_reply=0):
        aux = MessageAux()
        for v in aux_values:
            object_to_aux(v, aux)
        msg = DTXMessage(
            selector,
            channel_code=channel,
            identifier=identifier,
            conversation_index=conversation_index,
            expects_reply=expects_reply,
            auxiliaries=aux,
        )
        data = bytes(msg)
        return data[: dtx_message_header.sizeof()], data[dtx_message_header.sizeof() :]

    def test_reply_message_goes_to_queue(self):
        msg = self._msg(conversation_index=1, identifier=99)
        self.server._dispatch(msg)
        self.assertEqual(msg, self.server._reply_queues[99].get_nowait())

    def test_channel_push_invokes_channel_callback(self):
        received = []
        self.server._channel_callbacks[3] = received.append
        # 对端推送用二进制补码: channel 3 写成 0xFFFFFFFD (字面量, 不复用实现里的常量)
        msg = self._msg(channel=0xFFFFFFFD)
        self.server._dispatch(msg)
        self.assertEqual(1, len(received))

    def test_channel_code_arithmetic_matches_protocol(self):
        """回归: 通道号还原必须是 2**32 - code, 写成 0xFFFFFFFF - code 会整体偏 1。

        真机上 channel 2 的推送携带 0xFFFFFFFE, 若还原成 1 则消息全部落到兜底回调。
        """
        received = []
        self.server._channel_callbacks[2] = received.append
        self.server._dispatch(self._msg(channel=0xFFFFFFFE))
        self.assertEqual(1, len(received), "0xFFFFFFFE 应还原为 channel 2")

        # 反向确认: 偏 1 的通道不应命中
        self.server._dispatch(self._msg(channel=0xFFFFFFFE))
        self.assertEqual(2, len(received))
        self.assertNotIn(1, self.server._channel_callbacks)

    def test_selector_callback_invoked(self):
        received = []
        self.server._callbacks["finished:"] = received.append
        self.server._dispatch(self._msg(selector="finished:"))
        self.assertEqual(1, len(received))

    def test_undefined_callback_fallback(self):
        received = []
        self.server._undefined_callback = received.append
        self.server._dispatch(self._msg(selector="unknown:"))
        self.assertEqual(1, len(received))

    def test_expects_reply_triggers_ack(self):
        msg = self._msg(selector="push:", expects_reply=1, channel=5, identifier=8)
        self.server._dispatch(msg)
        self.server._client.send_dtx.assert_called_once()
        reply = self.server._client.send_dtx.call_args[0][1]
        self.assertEqual(8, reply.identifier)
        self.assertEqual(5, reply.channel_code)
        self.assertEqual(1, reply.conversation_index)  # 对端 index(0) + 1
        self.assertEqual(0x3, reply._flags)

    def test_ack_not_sent_for_channel_push(self):
        self.server._channel_callbacks[3] = lambda _: None
        msg = self._msg(channel=0xFFFFFFFD, expects_reply=1)
        self.server._dispatch(msg)
        self.server._client.send_dtx.assert_not_called()

    def test_enum_value(self):
        self.assertEqual("finished:", DTXEnum.FINISHED.value)


class TestDTXServerCall(unittest.TestCase):
    """_call 编码与同步等待。"""

    def setUp(self):
        self.server = DTXServer.__new__(DTXServer)
        self.server._cli = FakeSocket([])
        self.server._channels = {}
        self.server._reply_queues = defaultdict(queue.Queue)
        self.server._next_identifier = 1
        self.server._client = DTXClient()

    def test_call_encodes_and_waits_for_reply(self):
        reply = DTXMessage.decode(*TestDTXServerDispatch._msg_raw(conversation_index=1, identifier=1))
        result = {}

        def fake_wait(message_id, timeout=None):
            result["id"] = message_id
            return reply

        self.server.wait_reply = fake_wait
        ret = self.server._call(True, 7, "someMethod:", 42, "arg")
        self.assertEqual(1, result["id"])  # identifier 从 1 开始递增
        self.assertIs(reply, ret)
        sent = self.server._cli.sent[0]
        self.assertEqual(7, int.from_bytes(sent[24:28], "little"))  # header.channel

    def test_async_call_returns_none(self):
        ret = self.server._call(False, 7, "notify", 1)
        self.assertIsNone(ret)
        self.assertEqual(1, len(self.server._cli.sent))

    def test_identifier_increments(self):
        self.server.wait_reply = lambda message_id, timeout=None: DTXMessage()
        self.server._call(True, 0, "a")
        self.server._call(True, 0, "b")
        identifiers = [int.from_bytes(s[16:20], "little") for s in self.server._cli.sent]
        self.assertEqual([1, 2], identifiers)

    def test_wait_reply_timeout_raises_mux_error(self):
        self.server._reply_queues[123] = queue.Queue()
        with self.assertRaises(MuxError):
            self.server.wait_reply(123, timeout=0.01)

    def test_wait_reply_closed_raises_mux_error(self):
        self.server._reply_queues[123] = queue.Queue()
        self.server._reply_queues[123].put(None)
        with self.assertRaises(MuxError):
            self.server.wait_reply(123)


class TestReceiverShutdownLogging(unittest.TestCase):
    """主动 stop() 关闭连接不应产生 WARNING 噪音, 异常断开才告警。"""

    def _run_receiver(self, *, clean_stop):
        server = DTXServer.__new__(DTXServer)
        server._running = True
        server._client = DTXClient()
        server._callbacks = {}
        server._channel_callbacks = {}
        server._undefined_callback = None
        server._reply_queues = defaultdict(queue.Queue)
        server._recv_thread = None
        server.stop = lambda: None  # 隔离 stop 行为
        server._run_callbacks = lambda *a: None

        class ClosingSocket:
            """recv 立即 EOF; clean_stop 时先模拟 stop() 置位 _running。"""

            def recv(self, n):
                if clean_stop:
                    server._running = False
                return b""

            def send(self, data):
                return len(data)

            def close(self):
                pass

        server._cli = ClosingSocket()
        with self.assertLogs("Instrument", level="DEBUG") as logs:
            server._receiver()
        return [r.levelname for r in logs.records]

    def test_clean_stop_logs_debug(self):
        levels = self._run_receiver(clean_stop=True)
        self.assertNotIn("WARNING", levels)

    def test_unexpected_close_logs_warning(self):
        levels = self._run_receiver(clean_stop=False)
        self.assertIn("WARNING", levels)


class EchoSocket:
    """模拟 instrument 服务 socket: 阻塞式 recv, 设备侧数据预先/动态投递。"""

    def __init__(self):
        self.incoming = queue.Queue()
        self.sent = []
        self.closed = False
        self._buf = b""

    def push(self, data):
        """设备侧投递一段字节。"""
        self.incoming.put(bytes(data))

    def recv(self, n):
        while not self._buf:
            if self.closed:
                return b""
            try:
                self._buf = self.incoming.get(timeout=0.05)
            except queue.Empty:
                continue
        chunk, self._buf = self._buf[:n], self._buf[n:]
        return chunk

    def send(self, data):
        self.sent.append(bytes(data))
        return len(data)

    def close(self):
        self.closed = True


class TestDTXServerHandshake(unittest.TestCase):
    """完整握手流程: 接收线程 + 能力协商 + 同步应答 (模拟设备行为)。"""

    def _device_push(self, sock, **kw):
        kw.setdefault("selector", "_notifyOfPublishedCapabilities:")
        kw.setdefault("identifier", 100)  # 与客户端请求的 identifier(1) 区分, ack 会回显此值
        sock.push(make_message(**kw))

    def test_init_handshake(self):
        sock = EchoSocket()
        # 设备在连接建立后主动推送能力 (conversation_index=0, expects_reply=1)
        self._device_push(sock, aux_values=[[{"DTXConnection": 1}]], expects_reply=1)
        # 客户端能力请求 (identifier=1) 的应答 (conversation_index=1)
        sock.push(make_message(selector=None, identifier=1, conversation_index=1))

        server = DTXServer()
        try:
            server.init(sock)
            self.assertTrue(server.done.is_set())
            self.assertEqual([[{"DTXConnection": 1}]], server._published_capabilities)
            # 客户端发出了自己的能力请求 + 对设备推送的 ack (发送顺序与线程调度有关)
            self.assertEqual(2, len(sock.sent))
            decoded = [DTXMessage.decode(s[:32], s[32:]) for s in sock.sent]
            request = next(d for d in decoded if d.identifier == 1)
            self.assertEqual("_notifyOfPublishedCapabilities:", request.selector)
            self.assertEqual(
                [{"com.apple.private.DTXBlockCompression": 0, "com.apple.private.DTXConnection": 1}],
                request.auxiliaries,
            )
            # ack: 另一条发送的消息是 16 字节零 selector
            ack = next(d for d in decoded if d.identifier != 1)
            self.assertIsInstance(ack.selector, InstrumentRPCParseError)
        finally:
            server.stop()
        self.assertTrue(sock.closed)

    def test_call_roundtrip_through_thread(self):
        sock = EchoSocket()
        self._device_push(sock)
        sock.push(make_message(selector=None, identifier=1, conversation_index=1))
        server = DTXServer()
        try:
            server.init(sock)
            # 预置两个 RPC 应答: 通道创建 (identifier=2) 与实际调用 (identifier=3)
            sock.push(make_message(selector=None, identifier=2, conversation_index=1))
            sock.push(make_message(selector="reply-data", identifier=3, conversation_index=1))
            ret = server.call("com.apple.instruments.server.services.deviceinfo", "runningProcesses")
            self.assertEqual("reply-data", ret.selector)
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()

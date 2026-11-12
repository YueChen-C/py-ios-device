"""DTX 协议编解码单元测试 (ios_device.util.dtx_msg)。

纯离线测试: 只做字节构造与解析, 不需要真机。
"""

import plistlib
import unittest

from ios_device.util.bpylist2 import archive
from ios_device.util.dtx_msg import (
    DTXMessage,
    InfoRequest,
    MessageAux,
    RawInt32,
    RawInt32sl,
    RawInt64,
    RawInt64sl,
    RawObj,
    dtx_decode,
    dtx_message_aux,
    dtx_message_header,
    dtx_message_payload_header,
    object_to_aux,
    server_push_dtx_message_aux,
)
from ios_device.util.exceptions import InstrumentRPCParseError


def build_raw_message(
    *,
    flags=0x2,
    aux: bytes = b"",
    selector: bytes = b"",
    identifier=1,
    conversation_index=0,
    channel=0,
    expects_reply=0,
):
    """按 DTX 布局手工拼一条消息 (header + payload_header + aux + selector)。"""
    payload_header = dtx_message_payload_header.build(
        {"flags": flags, "aux_length": len(aux), "total_length": len(aux) + len(selector)}
    )
    payload = payload_header + aux + selector
    header = dtx_message_header.build(
        {
            "header_length": dtx_message_header.sizeof(),
            "payload_length": len(payload),
            "identifier": identifier,
            "conversation_index": conversation_index,
            "channel": channel,
            "expects_reply": expects_reply,
        }
    )
    return header, payload


class TestMessageAuxEncodeDecode(unittest.TestCase):
    """aux 值的编码与解码回环。"""

    def _roundtrip(self, aux: MessageAux):
        data = bytes(aux)
        return dtx_message_aux.parse(data).data

    def test_int32(self):
        items = self._roundtrip(object_to_aux(42, MessageAux()))
        self.assertEqual([(42, 3)], [(i.value, i.type) for i in items])

    def test_negative_int32(self):
        items = self._roundtrip(object_to_aux(-1, MessageAux()))
        self.assertEqual([(-1, 3)], [(i.value, i.type) for i in items])

    def test_uint64_boundaries(self):
        """修复回归: 旧版 0xFFFFFFFF / 2**31 走 int32 分支, build 时抛 FormatFieldError。"""
        for value in (2**31, 0xFFFFFFFF, 2**63, 2**64 - 1):
            with self.subTest(value=value):
                items = self._roundtrip(object_to_aux(value, MessageAux()))
                self.assertEqual([(value, 4)], [(i.value, i.type) for i in items])

    def test_negative_int64_boundaries(self):
        for value in (-(2**31) - 1, -(2**32), -(2**63)):
            with self.subTest(value=value):
                items = self._roundtrip(object_to_aux(value, MessageAux()))
                self.assertEqual([(value, 6)], [(i.value, i.type) for i in items])

    def test_int32_limits_stay_int32(self):
        for value in (2**31 - 1, -(2**31)):
            with self.subTest(value=value):
                items = self._roundtrip(object_to_aux(value, MessageAux()))
                self.assertEqual([(value, 3)], [(i.value, i.type) for i in items])

    def test_out_of_range_raises_value_error(self):
        for value in (2**64, -(2**63) - 1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    bytes(object_to_aux(value, MessageAux()))

    def test_bool_encoded_as_int(self):
        items = self._roundtrip(object_to_aux(True, MessageAux()))
        self.assertEqual([(1, 3)], [(i.value, i.type) for i in items])

    def test_object_roundtrip(self):
        obj = {"key": "value", "n": 1}
        items = self._roundtrip(object_to_aux(obj, MessageAux()))
        self.assertEqual(1, len(items))
        self.assertEqual(2, items[0].type)
        self.assertEqual(obj, items[0].value)

    def test_string_as_object(self):
        items = self._roundtrip(object_to_aux("execnameForPid:", MessageAux()))
        self.assertEqual([("execnameForPid:", 2)], [(i.value, i.type) for i in items])

    def test_multiple_values_in_one_aux(self):
        aux = MessageAux()
        object_to_aux(1, aux)
        object_to_aux("two", aux)
        object_to_aux(2**40, aux)
        items = self._roundtrip(aux)
        self.assertEqual([(1, 3), ("two", 2), (2**40, 4)], [(i.value, i.type) for i in items])

    def test_append_methods_chainable(self):
        aux = MessageAux().append_int(1).append_long(2).append_signed_long(-3).append_obj("x")
        items = self._roundtrip(aux)
        self.assertEqual([(1, 3), (2, 4), (-3, 6), ("x", 2)], [(i.value, i.type) for i in items])


class TestRawWrappers(unittest.TestCase):
    """Raw* 包装器强制指定编码类型。"""

    def _types(self, aux: MessageAux):
        return [(i.value, i.type) for i in dtx_message_aux.parse(bytes(aux)).data]

    def test_raw_obj_forces_object_encoding(self):
        self.assertEqual([(5, 2)], self._types(object_to_aux(RawObj(5), MessageAux())))

    def test_raw_obj_multiple(self):
        self.assertEqual([(1, 2), ("a", 2)], self._types(object_to_aux(RawObj(1, "a"), MessageAux())))

    def test_raw_int32sl(self):
        self.assertEqual([(-1, 3), (-2, 3)], self._types(object_to_aux(RawInt32sl(-1, -2), MessageAux())))

    def test_raw_int64sl(self):
        self.assertEqual([(-1, 6)], self._types(object_to_aux(RawInt64sl(-1), MessageAux())))

    def test_raw_int64(self):
        self.assertEqual([(7, 4)], self._types(object_to_aux(RawInt64(7), MessageAux())))

    def test_raw_int32(self):
        self.assertEqual([(7, 3)], self._types(object_to_aux(RawInt32(7), MessageAux())))

    def test_raw_int32sl_alias_of_raw_int32(self):
        """两个类编码结果一致 (DTX int32 本身就是有符号)。"""
        self.assertEqual(
            self._types(object_to_aux(RawInt32sl(-5), MessageAux())),
            self._types(object_to_aux(RawInt32(-5), MessageAux())),
        )


class TestInfoRequest(unittest.TestCase):
    def test_info_request_roundtrip(self):
        req = InfoRequest(items=["configurationInformation", "ktraceMachineInformation"])
        items = dtx_message_aux.parse(bytes(object_to_aux(req, MessageAux()))).data
        self.assertEqual(1, len(items))
        self.assertEqual(12, items[0].type)
        # Container 的 items 字段与 dict.items 方法重名, 需用下标访问
        self.assertEqual(req.items, list(items[0].value["items"]))

    def test_info_request_magic(self):
        req = InfoRequest(items=["a"])
        items = dtx_message_aux.parse(bytes(object_to_aux(req, MessageAux()))).data
        self.assertEqual("infoRequest", items[0].value.magic)


class TestDTXMessageRoundtrip(unittest.TestCase):
    """完整消息 encode -> decode 回环。"""

    def test_call_message_roundtrip(self):
        aux = MessageAux()
        object_to_aux(1234, aux)
        object_to_aux("arg", aux)
        msg = DTXMessage("someSelector:withArgs:", channel_code=7, identifier=42, expects_reply=True, auxiliaries=aux)
        header, payload = bytes(msg)[: dtx_message_header.sizeof()], bytes(msg)[dtx_message_header.sizeof() :]

        decoded = DTXMessage.decode(header, payload)
        self.assertEqual(42, decoded.identifier)
        self.assertEqual(7, decoded.channel_code)
        self.assertEqual(1, decoded.expects_reply)
        self.assertEqual(0, decoded.conversation_index)
        self.assertEqual("someSelector:withArgs:", decoded.selector)
        self.assertEqual([1234, "arg"], decoded.auxiliaries)

    def test_header_layout_is_stable(self):
        """消息头二进制布局不能变 (32 字节)。"""
        self.assertEqual(32, dtx_message_header.sizeof())
        self.assertEqual(16, dtx_message_payload_header.sizeof())
        raw = bytes(DTXMessage("x"))[:32]
        self.assertEqual(0x1F3D5B79, int.from_bytes(raw[0:4], "little"))
        self.assertEqual(32, int.from_bytes(raw[4:8], "little"))

    def test_empty_selector_and_aux(self):
        msg = DTXMessage(None, channel_code=3, identifier=9, expects_reply=False)
        decoded = DTXMessage.decode(*[bytes(msg)[:32], bytes(msg)[32:]])
        self.assertEqual(b"", decoded.selector)
        self.assertEqual([], decoded.auxiliaries)

    def test_selector_plist_bytes_sent_raw(self):
        """bytes selector 原样发送不再归档 (旧版行为), 编码后字节逐一致。"""
        payload_selector = plistlib.dumps({"raw": "selector"})
        msg = DTXMessage(payload_selector, channel_code=1, identifier=2)
        data = bytes(msg)
        self.assertIn(payload_selector, data)  # 未被二次归档
        decoded = DTXMessage.decode(data[:32], data[32:])
        self.assertEqual({"raw": "selector"}, decoded.selector)

    def test_unparseable_bytes_selector_kept_in_error(self):
        """ack 使用的 16 零字节 selector 解析失败时, 原始字节保留在 ParseError.data。"""
        payload_selector = b"\x00" * 16
        msg = DTXMessage(payload_selector, channel_code=1, identifier=2, flags=0x3)
        data = bytes(msg)
        decoded = DTXMessage.decode(data[:32], data[32:])
        self.assertIsInstance(decoded.selector, InstrumentRPCParseError)
        self.assertEqual(payload_selector, decoded.selector.data)


class TestDTXMessageDecode(unittest.TestCase):
    def test_plist_selector(self):
        selector = plistlib.dumps({"some": "data"})
        header, payload = build_raw_message(selector=selector)
        decoded = DTXMessage.decode(header, payload)
        self.assertEqual({"some": "data"}, decoded.selector)

    def test_archived_selector(self):
        selector = archive({"archived": True})
        header, payload = build_raw_message(selector=selector)
        decoded = DTXMessage.decode(header, payload)
        self.assertEqual({"archived": True}, decoded.selector)

    def test_unparseable_selector_becomes_error(self):
        header, payload = build_raw_message(selector=b"\xff\xff\xff\xff not a plist")
        decoded = DTXMessage.decode(header, payload)
        self.assertIsInstance(decoded.selector, InstrumentRPCParseError)
        self.assertEqual(b"\xff\xff\xff\xff not a plist", decoded.selector.data)

    def test_empty_payload(self):
        header, payload = build_raw_message()
        payload = payload[:0]  # payload_length 为 0
        header = dtx_message_header.build(
            {
                "header_length": 32,
                "payload_length": 0,
                "identifier": 5,
                "conversation_index": 0,
                "channel": 0,
                "expects_reply": 0,
            }
        )
        decoded = DTXMessage.decode(header, b"")
        self.assertEqual(5, decoded.identifier)
        self.assertIsNone(decoded.selector)

    def test_total_length_zero(self):
        header, payload = build_raw_message()
        decoded = DTXMessage.decode(header, payload)
        self.assertEqual([], decoded.auxiliaries)
        self.assertIsNone(decoded.selector)

    def test_aux_without_selector(self):
        aux = bytes(object_to_aux(77, MessageAux()))
        header, payload = build_raw_message(aux=aux)
        decoded = DTXMessage.decode(header, payload)
        self.assertEqual([77], decoded.auxiliaries)
        self.assertEqual(b"", decoded.selector)

    def test_decode_accepts_bytearray(self):
        """recv_dtx 传入的是 bytearray。"""
        aux = bytes(object_to_aux(5, MessageAux()))
        header, payload = build_raw_message(aux=aux, selector=archive("sel"))
        decoded = DTXMessage.decode(bytearray(header), bytearray(payload))
        self.assertEqual([5], decoded.auxiliaries)
        self.assertEqual("sel", decoded.selector)

    def test_server_push_alias_identical(self):
        self.assertIs(server_push_dtx_message_aux, dtx_message_aux)

    def test_dtx_decode_alias(self):
        """别名可调用且指向同一实现 (bound method 每次访问都是新对象, 用结果比较)。"""
        header, payload = build_raw_message(selector=plistlib.dumps([1]))
        self.assertEqual(DTXMessage.decode(header, payload).selector, dtx_decode(header, payload).selector)

    def test_repr_is_informative(self):
        msg = DTXMessage("selector:")
        self.assertIn("DTXMessage", repr(msg))
        self.assertIn("selector:", repr(msg))


class TestDecodedMessageDefaults(unittest.TestCase):
    """构造出的消息 (未解码) 的属性读取不应崩溃。"""

    def test_built_message_properties(self):
        msg = DTXMessage("sel", channel_code=9, identifier=3, expects_reply=True)
        self.assertEqual(3, msg.identifier)
        self.assertEqual(9, msg.channel_code)
        self.assertEqual(1, msg.expects_reply)
        self.assertEqual(0, msg.conversation_index)

    def test_defaults(self):
        msg = DTXMessage()
        self.assertEqual(0, msg.identifier)
        self.assertEqual(0, msg.channel_code)
        self.assertEqual(0, msg.expects_reply)
        self.assertEqual(None, msg.selector)


if __name__ == "__main__":
    unittest.main()

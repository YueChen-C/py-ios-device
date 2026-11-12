"""DTX 协议消息的构造与解析。

协议参考: https://github.com/troybowman/dtxmsg
DTX 消息按顺序分为四层:
1. DTXMessageHeader        消息头 (``dtx_message_header``)
2. DTXMessagePayloadHeader 载荷头 (``dtx_message_payload_header``)
3. DTXMessageAux           辅助参数 (``dtx_message_aux``)
4. selector                方法名/返回值, NSKeyedArchiver 或 plist 编码
"""

import plistlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar, List, Optional, Union

from construct import (
    Adapter,
    Array,
    Const,
    CString,
    Default,
    GreedyBytes,
    GreedyRange,
    Int16ul,
    Int32sl,
    Int32ul,
    Int64sl,
    Int64ul,
    Prefixed,
    Select,
    Struct,
    Switch,
    this,
)

from ios_device.util.variables import LOG

from . import Log
from .bpylist2 import archive, unarchive
from .exceptions import InstrumentRPCParseError

log = Log.getLogger(LOG.Instrument.value)

# DTX aux 值类型 (见 dtxmsg)
AUX_TYPE_BYTES = 1  # 长度前缀字节串
AUX_TYPE_OBJECT = 2  # NSKeyedArchiver 归档对象
AUX_TYPE_INT32 = 3  # 有符号 int32
AUX_TYPE_UINT64 = 4  # 无符号 int64
AUX_TYPE_UINT32 = 5  # 无符号 int32
AUX_TYPE_INT64 = 6  # 有符号 int64
AUX_TYPE_INFO_REQUEST = 12  # infoRequest

INT32_MIN, INT32_MAX = -(2**31), 2**31 - 1
INT64_MIN, INT64_MAX = -(2**63), 2**63 - 1
UINT64_MAX = 2**64 - 1


class Raw:
    """参数类型包装器基类。

    普通 int 会按取值范围自动选择编码类型; 需要精确控制类型
    (如强制有符号、按对象编码)时, 用这些包装类传入 call 的辅助参数。
    """


class RawObj(Raw):
    """把每个参数按对象 (NSKeyedArchiver) 编码, 例如 PID 需要以对象形式传递。"""

    def __init__(self, *data: Any):
        self.data = data


class RawInt64sl(Raw):
    """把每个参数编码为有符号 int64 (type 6)。"""

    def __init__(self, *data: int):
        self.data = data


class RawInt32sl(Raw):
    """把每个参数编码为有符号 int32 (type 3)。DTX 的 int32 本身就是有符号, 与 RawInt32 等价, 保留命名兼容。"""

    def __init__(self, *data: int):
        self.data = data


class RawInt64(Raw):
    """把每个参数编码为无符号 int64 (type 4)。"""

    def __init__(self, *data: int):
        self.data = data


class RawInt32(Raw):
    """把每个参数编码为 int32 (type 3)。"""

    def __init__(self, *data: int):
        self.data = data


@dataclass
class InfoRequest:
    """deviceinfo 服务的 infoRequest 参数 (aux type 12)。"""

    magic: ClassVar[str] = "infoRequest"
    items: List[str]


class PlistAdapter(Adapter):
    """construct 字节串 <-> NSKeyedArchiver 归档对象。"""

    def _decode(self, obj, context, path):
        return unarchive(obj)

    def _encode(self, obj, context, path):
        return archive(obj)


info_request_struct = Struct(
    "magic" / CString("utf8"), "count" / Int32ul, "items" / Array(this.count, Prefixed(Int32ul, CString("utf8")))
)


class InfoReqAdapter(Adapter):
    """construct 字节串 <-> InfoRequest。"""

    def _decode(self, obj, ctx, path):
        return info_request_struct.parse(obj)

    def _encode(self, obj: InfoRequest, ctx, path):
        return info_request_struct.build({"magic": obj.magic, "count": len(obj.items), "items": obj.items})


dtx_message_header = Struct(
    "magic" / Const(0x1F3D5B79, Int32ul),
    "header_length" / Int32ul,
    "fragment_id" / Default(Int16ul, 0),
    "fragment_count" / Default(Int16ul, 1),
    "payload_length" / Int32ul,
    "identifier" / Int32ul,
    "conversation_index" / Int32ul,
    "channel" / Int32ul,
    "expects_reply" / Int32ul,
)

dtx_message_payload_header = Struct(
    "flags" / Int32ul,
    "aux_length" / Int32ul,
    "total_length" / Int64ul,
)

_aux_item = Struct(
    "magic" / Select(Const(0xA, Int32ul), Int32ul),
    "type" / Int32ul,
    "value"
    / Switch(
        this.type,
        {
            AUX_TYPE_BYTES: Prefixed(Int32ul, GreedyBytes),
            AUX_TYPE_OBJECT: PlistAdapter(Prefixed(Int32ul, GreedyBytes)),
            AUX_TYPE_INT32: Int32sl,
            AUX_TYPE_UINT64: Int64ul,
            AUX_TYPE_UINT32: Int32ul,
            AUX_TYPE_INT64: Int64sl,
            AUX_TYPE_INFO_REQUEST: InfoReqAdapter(GreedyBytes),
        },
        default=GreedyBytes,
    ),
)

dtx_message_aux = Struct(
    "magic" / Default(Int64ul, 0x1F0),
    "data" / Prefixed(Int64ul, GreedyRange(_aux_item)),
)

# 历史上 server push 消息的 aux 结构与请求不同, 现在两者完全一致, 保留别名兼容旧引用
server_push_dtx_message_aux = dtx_message_aux


class MessageAux:
    """DTX 辅助参数 (aux) 构造器。

    链式调用 ``append_*`` 后通过 ``bytes()`` 编码。
    """

    def __init__(self) -> None:
        self.values: List[dict] = []

    def append_int(self, value: int) -> "MessageAux":
        """有符号 int32 (type 3)。"""
        self.values.append({"type": AUX_TYPE_INT32, "value": value})
        return self

    def append_long(self, value: int) -> "MessageAux":
        """无符号 int64 (type 4)。"""
        self.values.append({"type": AUX_TYPE_UINT64, "value": value})
        return self

    def append_signed_int(self, value: int) -> "MessageAux":
        """有符号 int32, 与 append_int 等价, 保留命名兼容。"""
        self.values.append({"type": AUX_TYPE_INT32, "value": value})
        return self

    def append_signed_long(self, value: int) -> "MessageAux":
        """有符号 int64 (type 6)。"""
        self.values.append({"type": AUX_TYPE_INT64, "value": value})
        return self

    def append_obj(self, value: Any) -> "MessageAux":
        """NSKeyedArchiver 归档对象 (type 2)。"""
        self.values.append({"type": AUX_TYPE_OBJECT, "value": value})
        return self

    def append_info(self, value: InfoRequest) -> "MessageAux":
        """infoRequest 请求 (type 12)。"""
        self.values.append({"type": AUX_TYPE_INFO_REQUEST, "value": value, "magic": 1})
        return self

    def __bytes__(self) -> bytes:
        return dtx_message_aux.build({"data": self.values})


class DTXMessage:
    """一条 DTX 消息, 同时承担编码与解码两个角色。

    编码发送: 构造时给出 ``selector`` / ``auxiliaries`` 等参数, 再 ``bytes(msg)``;
    解码接收: 使用 :meth:`decode`, 之后 ``auxiliaries`` 为参数值列表,
    ``identifier`` / ``channel_code`` 等属性从消息头读取。
    """

    FLAG_DEFAULT = 0x2

    def __init__(
        self,
        selector: Any = None,
        *,
        channel_code: int = 0,
        identifier: int = 0,
        conversation_index: int = 0,
        expects_reply: bool = False,
        flags: int = FLAG_DEFAULT,
        auxiliaries: Optional[MessageAux] = None,
    ):
        self._selector = selector
        self._channel_code = channel_code
        self._identifier = identifier
        self._conversation_index = conversation_index
        self._expects_reply = expects_reply
        self._flags = flags
        self.auxiliaries: Union[MessageAux, list] = auxiliaries if auxiliaries is not None else MessageAux()
        # 以下由 decode 填充
        self._message_header = None
        self._payload_header = None

    @classmethod
    def decode(cls, header_data: Union[bytes, bytearray], payload_data: Union[bytes, bytearray]) -> "DTXMessage":
        """从消息头字节与载荷字节解码一条 DTX 消息。"""
        msg = cls()
        msg.auxiliaries = []
        msg._message_header = dtx_message_header.parse(header_data)
        if msg._message_header.payload_length <= 0:
            return msg

        payload_header_size = dtx_message_payload_header.sizeof()
        msg._payload_header = dtx_message_payload_header.parse(payload_data[:payload_header_size])
        if msg._payload_header.total_length == 0:
            return msg

        aux_length = msg._payload_header.aux_length
        if aux_length:
            aux = dtx_message_aux.parse(payload_data[payload_header_size : payload_header_size + aux_length])
            msg.auxiliaries = [item.value for item in aux.data]
        msg._selector = cls._parse_selector(payload_data[payload_header_size + aux_length :])
        log.debug(f"DTX msg decode: {msg.selector} :{msg.auxiliaries}")
        return msg

    @staticmethod
    def _parse_selector(data: Union[bytes, bytearray]) -> Any:
        """解析 selector 载荷: 依次尝试 NSKeyedArchiver 与 plist, 均失败则返回 InstrumentRPCParseError。"""
        if not data:
            return bytes(data)
        data = bytes(data)
        for parse in (unarchive, plistlib.loads):  # NSKeyedArchiver or Plist
            try:
                return parse(data)
            except Exception as e:  # 对端数据不可信, 任意解析异常都需要兜底
                log.debug(f"selector parse with {parse.__name__} failed: {e!r}")
        return InstrumentRPCParseError(data)

    def __bytes__(self) -> bytes:
        aux = bytes(self.auxiliaries) if isinstance(self.auxiliaries, MessageAux) else b""
        if isinstance(self._selector, (bytes, bytearray, memoryview)):
            sel = bytes(self._selector)
        elif self._selector is None:
            sel = b""
        else:
            sel = archive(self._selector)
        payload_header = dtx_message_payload_header.build(
            {"flags": self._flags, "aux_length": len(aux), "total_length": len(aux) + len(sel)}
        )
        message_header = dtx_message_header.build(
            {
                "header_length": dtx_message_header.sizeof(),
                "payload_length": dtx_message_payload_header.sizeof() + len(aux) + len(sel),
                "identifier": self._identifier,
                "conversation_index": self._conversation_index,
                "channel": self._channel_code,
                "expects_reply": int(bool(self._expects_reply)),
            }
        )
        return message_header + payload_header + aux + sel

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.identifier} channel={self.channel_code} "
            f"selector={repr(self.selector)[:100]}>"
        )

    @property
    def identifier(self) -> int:
        """消息标识 (解码消息来自消息头)。"""
        if self._message_header is not None:
            return self._message_header.identifier
        return self._identifier

    @property
    def channel_code(self) -> int:
        """通道编码 (解码消息来自消息头)。"""
        if self._message_header is not None:
            return self._message_header.channel
        return self._channel_code

    @property
    def expects_reply(self) -> int:
        """是否需要回复 (解码消息来自消息头)。"""
        if self._message_header is not None:
            return self._message_header.expects_reply
        return int(bool(self._expects_reply))

    @property
    def conversation_index(self) -> int:
        """会话序号 (解码消息来自消息头)。"""
        if self._message_header is not None:
            return self._message_header.conversation_index
        return self._conversation_index

    @property
    def selector(self) -> Any:
        """方法名/返回值, 解析失败时为 InstrumentRPCParseError。"""
        return self._selector

    @property
    def raw(self):
        """解码后的原始消息头 (construct Container), 兼容旧 API。"""
        return self._message_header


def object_to_aux(arg: Any, aux: MessageAux) -> MessageAux:
    """把任意 Python 参数追加为 DTX aux 值。

    - int: 按取值范围自动选择 int32 / uint64 / int64 (bool 按 0/1 编码)
    - Enum: 按 ``.value`` 归档为对象
    - Raw* 包装器: 强制指定编码类型, 逐个元素追加
    - InfoRequest: 编码为 infoRequest (type 12)
    - 其他: NSKeyedArchiver 归档为对象
    """
    if isinstance(arg, Raw):
        if isinstance(arg, RawObj):
            for item in arg.data:
                aux.append_obj(item)
        elif isinstance(arg, RawInt32sl):
            for item in arg.data:
                aux.append_signed_int(item)
        elif isinstance(arg, RawInt64sl):
            for item in arg.data:
                aux.append_signed_long(item)
        elif isinstance(arg, RawInt64):
            for item in arg.data:
                aux.append_long(item)
        elif isinstance(arg, RawInt32):
            for item in arg.data:
                aux.append_int(item)
    elif isinstance(arg, int):
        # bool 是 int 的子类, 按数值 0/1 编码 (与旧版一致)
        if INT32_MIN <= arg <= INT32_MAX:
            aux.append_int(arg)
        elif 0 <= arg <= UINT64_MAX:
            aux.append_long(arg)
        elif INT64_MIN <= arg < 0:
            aux.append_signed_long(arg)
        else:
            raise ValueError(f"int out of DTX aux range: {arg}")
    elif isinstance(arg, Enum):
        aux.append_obj(arg.value)
    elif isinstance(arg, InfoRequest):
        aux.append_info(arg)
    else:
        aux.append_obj(arg)
    return aux


dtx_decode = DTXMessage.decode

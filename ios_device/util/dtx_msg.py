"""
dtx massage 协议头
参考 https://github.com/troybowman/dtxmsg
大会 PPT
dtx msg 分为几层，按顺序
1.DTXMessageHeader 头部定义
2.DTXMessagePayloadHeader  DTX Body 数据头定义
3.DTXMessageAux Aux数据
4.CFStringRef 类型数据类型 method 请求的方法声明
"""
import io
import plistlib
from abc import ABC
from enum import Enum

from construct import Struct, Int32ul, Int16ul, Int64ul, Const, Prefixed, GreedyBytes, this, Adapter, Select, \
    GreedyRange, Switch, Default
from ios_device.util.variables import LOG

from . import Log
from .bpylist2 import unarchive, archive
from .exceptions import InstrumentRPCParseError

log = Log.getLogger(LOG.Instrument.value)


class RawObj:
    """ 某些情况 int 类型需要转成 obj
    """

    def __init__(self, *data):
        self.data = data


class PlistAdapter(Adapter, ABC):
    def _decode(self, obj, context, path):
        return unarchive(obj)

    def _encode(self, obj, context, path):
        return archive(obj)


dtx_message_header = Struct(
    'magic' / Const(0x1F3D5B79, Int32ul),
    'header_length' / Int32ul,
    'fragment_id' / Default(Int16ul, 0),
    'fragment_count' / Default(Int16ul, 1),
    'payload_length' / Int32ul,
    'identifier' / Int32ul,
    'conversation_index' / Int32ul,
    'channel' / Int32ul,
    'expects_reply' / Int32ul,
)

dtx_message_payload_header = Struct(
    'flags' / Int32ul,
    'aux_length' / Int32ul,
    'total_length' / Int64ul,
)

dtx_message_aux = Struct(
    'magic' / Default(Int64ul, 0x1f0),
    'data' / Prefixed(Int64ul, GreedyRange(Struct(
        'magic' / Select(Const(0xa, Int32ul), Int32ul),
        'type' / Int32ul,
        'value' / Switch(this.type,
                         {2: PlistAdapter(Prefixed(Int32ul, GreedyBytes)), 3: Int32ul, 4: Int64ul, 5: Int32ul,
                          6: Int64ul},
                         default=GreedyBytes),
    )))
)


class MessageAux:
    def __init__(self):
        self.values = []

    def append_int(self, value: int):
        self.values.append({'type': 3, 'value': value})
        return self

    def append_long(self, value: int):
        self.values.append({'type': 4, 'value': value})
        return self

    def append_obj(self, value):
        self.values.append({'type': 2, 'value': value})
        return self

    def __bytes__(self):
        return dtx_message_aux.build(dict(data=self.values))


class DTXMessage:
    _FLAGS_TYPE = 2

    def __init__(self):
        self._buf = b''
        self._message_header = None
        self._payload_header = None
        self._identifier = None
        self._channel_code = None
        self._expects_reply = None
        self._selector = None
        self._conversation_index = 0
        self._flags = self._FLAGS_TYPE
        self.auxiliaries: MessageAux = MessageAux()

    @classmethod
    def decode(cls, header_data: bytes, payload_data: bytes):
        ret = DTXMessage()
        ret._buf = payload_data
        payload_io = io.BytesIO(payload_data)
        ret._message_header = dtx_message_header.parse(header_data)
        if not ret._message_header.payload_length > 0:
            return ret

        ret._payload_header = dtx_message_payload_header.parse(payload_io.read(dtx_message_payload_header.sizeof()))
        if ret._payload_header.total_length == 0:
            return ret
        if ret._payload_header.aux_length:
            auxiliaries = dtx_message_aux.parse(payload_io.read(ret._payload_header.aux_length)).data
            ret.auxiliaries = [i.value for i in auxiliaries]
        else:
            ret.auxiliaries = []

        data = payload_io.read()
        for fun in (unarchive, plistlib.loads):  # NSKeyedArchived or Plist
            try:
                ret._selector = fun(data)
            except:
                ret._selector = InstrumentRPCParseError(data)
            else:
                break
        payload_io.close()
        log.debug(f'DTX msg decode: {ret.selector} :{ret.auxiliaries}')
        return ret

    def __bytes__(self) -> bytes:
        aux = bytes(self.auxiliaries) if self.auxiliaries is not None else b''
        if isinstance(self._selector, bytes):
            sel = self._selector
        else:
            sel = archive(self._selector) if self._selector is not None else b''
        payload_header = dtx_message_payload_header.build(
            dict(flags=self._flags, aux_length=len(aux), total_length=len(aux) + len(sel)))
        message_header = dtx_message_header.build(dict(
            header_length=dtx_message_header.sizeof(),
            payload_length=dtx_message_payload_header.sizeof() + len(aux) + len(sel),
            identifier=self._identifier,
            conversation_index=self._conversation_index,
            channel=self._channel_code,
            expects_reply=1 if self._expects_reply else 0
        ))
        payload_buf = message_header + payload_header + aux + sel
        return payload_buf

    @property
    def identifier(self):
        return self._message_header.identifier

    @property
    def channel_code(self):
        return self._message_header.channel

    @property
    def expects_reply(self):
        return self._message_header.expects_reply

    @property
    def selector(self):
        return self._selector

    @property
    def conversation_index(self):
        return self._message_header.conversation_index


def object_to_aux(arg, aux: MessageAux):
    if isinstance(arg, int) and not isinstance(arg, RawObj):
        if abs(arg) < (2 ** 32):
            aux.append_int(arg)
        elif abs(arg) < (2 ** 64):
            aux.append_long(arg)
        else:
            raise ValueError("num too large")
    else:
        if isinstance(arg, Enum):
            arg = arg.value
        if isinstance(arg, RawObj):
            arg = arg.data
            for i in arg:
                aux.append_obj(i)
            return aux
        aux.append_obj(arg)
    return aux


dtx_decode = DTXMessage.decode

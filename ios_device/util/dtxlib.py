"""
dtx massage 协议头
参考 https://github.com/troybowman/dtxmsg
dtx msg 分为几层，按顺序
1.DTXMessageHeader 头部定义
2.DTXMessagePayloadHeader  DTX Body 数据头定义
3.Body 构造数据流
4.CFStringRef 类型数据类型 method 请求的方法声明

"""
import struct
from ctypes import Structure, \
    c_uint32, c_uint16, c_uint64, c_int64, sizeof


from .bpylist import unarchive, archive


def div_ceil(p: int, q: int) -> int:
    return (p + q - 1) // q


class DTXMessageHeader(Structure):
    _fields_ = [
        ('magic', c_uint32),
        ('cb', c_uint32),
        ('fragmentId', c_uint16),
        ('fragmentCount', c_uint16),
        ('length', c_uint32),
        ('identifier', c_uint32),
        ('conversationIndex', c_uint32),
        ('channelCode', c_uint32),
        ('expectsReply', c_uint32)
    ]

    def __init__(self):
        super().__init__()
        self.magic = 0x1f3d5b79
        self.cb = sizeof(DTXMessageHeader)
        self.fragmentId = 0
        self.fragmentCount = 1


class DTXMessagePayloadHeader(Structure):
    _fields_ = [
        ('flags', c_uint32),
        ('auxiliaryLength', c_uint32),
        ('totalLength', c_uint64)
    ]

    def __init__(self):
        super().__init__()
        self.flags = 0x2


class DTXAuxiliariesHeader(Structure):
    _fields_ = [
        ('magic', c_uint64),
        ('length', c_int64)
    ]

    def __init__(self):
        super().__init__()
        self.magic = 0x1f0


class DTXMessage:
    def __init__(self):
        self._buf = b''
        self._message_header = DTXMessageHeader()
        self._payload_header = None
        self._auxiliaries_header = None
        self._selector = b''
        self._auxiliaries = []

    def _init_payload_header(self):
        """ 构造 DTXMessagePayload 头部
        :return:
        """
        if self._payload_header is None:
            self._payload_header = DTXMessagePayloadHeader()
            self._payload_header.totalLength = 0
            self._message_header.length += sizeof(DTXMessagePayloadHeader)

    def _init_auxiliaries_header(self):
        self._init_payload_header()
        if self._auxiliaries_header is None:
            self._auxiliaries_header = DTXAuxiliariesHeader()
            self._payload_header.totalLength += sizeof(DTXAuxiliariesHeader)
            self._payload_header.auxiliaryLength += sizeof(DTXAuxiliariesHeader)
            self._message_header.length += sizeof(DTXAuxiliariesHeader)

    def _update_auxiliary_len(self, delta):
        self._message_header.length += delta
        self._payload_header.totalLength += delta
        self._payload_header.auxiliaryLength += delta
        self._auxiliaries_header.length += delta
        pass

    def _update_selector_len(self, delta):
        self._message_header.length += delta
        self._payload_header.totalLength += delta
        pass

    @classmethod
    def from_bytes(self, buffer: bytes):
        cursor = 0
        ret = DTXMessage()
        backup_buf = buffer
        ret._buf = buffer
        payload_buf = b''
        ret._message_header = DTXMessageHeader.from_buffer_copy(buffer[cursor:cursor + sizeof(DTXMessageHeader)])
        cursor = sizeof(DTXMessageHeader)
        has_payload = ret._message_header.length > 0
        if not has_payload:
            return ret
        if ret._message_header.length != len(buffer) - cursor - (ret._message_header.fragmentCount - 1) * sizeof(
                DTXMessageHeader):

            raise ValueError(f"incorrect DTXMessageHeader {ret._message_header.length} -> length:{len(buffer)}")

        if ret._message_header.fragmentCount == 1:
            payload_buf = buffer[cursor:]
        else:
            assert ret._message_header.fragmentCount >= 3
            while cursor < len(buffer):
                subhdr = DTXMessageHeader.from_buffer_copy(buffer[cursor: cursor + sizeof(DTXMessageHeader)])
                cursor += sizeof(DTXMessageHeader)
                assert len(buffer[cursor: cursor + subhdr.length]) == subhdr.length
                payload_buf += buffer[cursor: cursor + subhdr.length]
                cursor += subhdr.length
                # print(subhdr.magic, subhdr.fragmentCount, subhdr.fragmentId, subhdr.length)
                assert subhdr.magic == ret._message_header.magic
            assert cursor == len(buffer)
        buffer = payload_buf
        cursor = 0
        ret._payload_header = DTXMessagePayloadHeader.from_buffer_copy(
            buffer[cursor:cursor + sizeof(DTXMessagePayloadHeader)])
        cursor += sizeof(DTXMessagePayloadHeader)
        if ret._payload_header.totalLength == 0:
            return ret
        if ret._payload_header.totalLength != len(buffer) - cursor:
            raise ValueError("incorrect DTXPayloadHeader->totalLength")
        if ret._payload_header.auxiliaryLength:
            ret._auxiliaries_header = DTXAuxiliariesHeader.from_buffer_copy(
                buffer[cursor:cursor + sizeof(DTXAuxiliariesHeader)])
            cursor += sizeof(DTXAuxiliariesHeader)
            i = 0
            while i < ret._auxiliaries_header.length:
                m, t = struct.unpack("<II", buffer[cursor + i: cursor + i + 8])
                if m != 0xa:  # magic
                    raise ValueError("incorrect auxiliary magic")
                if t == 2:  # CFStringRef
                    l, = struct.unpack("<I", buffer[cursor + i + 8: cursor + i + 12])
                    ret._auxiliaries.append(buffer[cursor + i: cursor + i + 12 + l])
                    i += 12 + l
                elif t == 3:  # int32_t
                    ret._auxiliaries.append(buffer[cursor + i: cursor + i + 12])
                    i += 12
                elif t == 4:  # int64_t
                    ret._auxiliaries.append(buffer[cursor + i: cursor + i + 16])
                    i += 16
                elif t == 6:
                    ret._auxiliaries.append(buffer[cursor + i: cursor + i + 16])
                    i += 16
                else:
                    raise ValueError("unknown auxiliary type")
            if i != ret._auxiliaries_header.length:
                raise ValueError("incorrect DTXAuxiliariesHeader.length")
            cursor += ret._auxiliaries_header.length
        ret._selector = buffer[cursor:]
        assert ret.to_bytes() == backup_buf, "correctness check"
        return ret

    def to_bytes(self) -> bytes:
        if not self._payload_header:
            return self._buf
        payload_buf = b''
        payload_buf += bytes(self._payload_header)
        if self._auxiliaries_header:
            payload_buf += bytes(self._auxiliaries_header)
            if self._auxiliaries:
                payload_buf += b''.join(self._auxiliaries)
        payload_buf += self._selector
        if len(payload_buf) > 65504:
            parts = div_ceil(len(payload_buf), 65504)
            self._message_header.fragmentCount = parts + 1
            self._buf = bytes(self._message_header)
            for part in range(parts):
                part_len = min(len(payload_buf) - part * 65504, 65504)
                subhdr = DTXMessageHeader.from_buffer_copy(bytes(self._message_header))
                subhdr.fragmentId = part + 1
                subhdr.length = part_len
                self._buf += bytes(subhdr)
                self._buf += payload_buf[part * 65504: part * 65504 + part_len]
        else:
            self._buf = bytes(self._message_header) + payload_buf
        return self._buf

    def set_selector(self, buffer: bytes):
        self._init_payload_header()
        self._update_selector_len(len(buffer) - len(self._selector))
        self._selector = buffer
        return self

    def get_selector(self) -> bytes:
        return self._selector

    def add_auxiliary(self, buffer: bytes):
        self._init_auxiliaries_header()
        self._update_auxiliary_len(len(buffer))
        self._auxiliaries.append(buffer)
        return self

    def get_auxiliary_count(self) -> int:
        return len(self._auxiliaries)

    def get_auxiliary_at(self, idx: int) -> bytes:
        return self._auxiliaries[idx]

    def new_reply(self):
        ret = DTXMessage()
        ret.channel_code = self.channel_code
        ret.identifier = self.identifier
        ret.conversation_index = self.conversation_index + 1
        return ret

    @property
    def conversation_index(self):
        return self._message_header.conversationIndex

    @conversation_index.setter
    def conversation_index(self, idx: int):
        self._message_header.conversationIndex = idx
        return self

    @property
    def channel_code(self):
        return self._message_header.channelCode

    @channel_code.setter
    def channel_code(self, channel: int):
        self._message_header.channelCode = channel
        return self

    @property
    def identifier(self):
        return self._message_header.identifier

    @identifier.setter
    def identifier(self, identifier: int):
        self._message_header.identifier = identifier
        return self

    @property
    def expects_reply(self):
        return self._message_header.expectsReply

    @expects_reply.setter
    def expects_reply(self, expect: bool):
        self._message_header.expectsReply = 1 if expect else 0


def ns_keyed_archiver(obj):
    return archive(obj)


def pyobject_to_auxiliary(var):
    if isinstance(var,int):
        if abs(var) < 2 ** 32:
            return struct.pack('<iii', 0xa, 3, var)
        elif abs(var) < 2 ** 64:
            return struct.pack('<iiq', 0xa, 4, var)
        else:
            raise ValueError("num too large")
    else:
        buf = ns_keyed_archiver(var)
        return struct.pack('<iii', 0xa, 2, len(buf)) + buf


def auxiliary_to_pyobject(aux):
    m, t = struct.unpack("<ii", aux[:8])
    if m != 0xa:
        raise ValueError("auxiliary magic error")
    if t == 2:  # CFTypeRef object
        l, = struct.unpack("<i", aux[8: 12])
        assert len(aux) == 12 + l, "bad auxiliary"
        return unarchive(aux[12:])
    elif t == 3:  # int32_t
        n, = struct.unpack("<i", aux[8:12])
        return n
    elif t == 4:  # int64_t
        n, = struct.unpack("<q", aux[8:16])
        return n
    elif t == 6:
        n = struct.unpack("<LL", aux[8:16])
        return n
    else:
        raise ValueError("unknown auxiliary type")


def get_auxiliary_text(dtx):
    _list = []
    if dtx._auxiliaries:
        for buf in dtx._auxiliaries:
            _list.append(auxiliary_to_pyobject(buf))
    return _list


def pyobject_to_selector(s):
    return archive(s)


def selector_to_pyobject(sel):
    if not sel:
        return None
    return unarchive(sel)

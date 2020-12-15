"""
dtx massage 协议头
参考 https://github.com/troybowman/dtxmsg
"""
import struct
from ctypes import Structure, \
    c_uint32, c_uint16, c_uint64, c_int64, sizeof

from instrument.bpylist import archiver


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
        ret._buf = buffer
        payload_buf = b''
        ret._message_header = DTXMessageHeader.from_buffer_copy(buffer[cursor:cursor + sizeof(DTXMessageHeader)])  # 头长度
        cursor = sizeof(DTXMessageHeader)
        has_payload = ret._message_header.length > 0
        if not has_payload:
            return ret

        if ret._message_header.length != len(buffer) - cursor - (ret._message_header.fragmentCount - 1) * sizeof(
                DTXMessageHeader):
            raise ValueError("incorrect DTXMessageHeader->length")

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
                assert subhdr.magic == ret._message_header.magic
            assert cursor == len(buffer)
        buffer = payload_buf
        cursor = 0
        ret._payload_header = DTXMessagePayloadHeader.from_buffer_copy(
            buffer[cursor:cursor + sizeof(DTXMessagePayloadHeader)])  # 包体长度
        cursor += sizeof(DTXMessagePayloadHeader)
        if ret._payload_header.totalLength == 0:
            return ret
        if ret._payload_header.totalLength != len(buffer) - cursor:
            raise ValueError("incorrect DTXPayloadHeader->totalLength")
        if ret._payload_header.auxiliaryLength:
            ret._auxiliaries_header = DTXAuxiliariesHeader.from_buffer_copy(
                buffer[cursor:cursor + sizeof(DTXAuxiliariesHeader)])
            cursor += sizeof(DTXAuxiliariesHeader)
            cursor += ret._auxiliaries_header.length
        ret._selector = buffer[cursor:]
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
    return archiver.archive(obj)


def pyobject_to_auxiliary(var):
    if type(var) is int:
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
    if t == 2:
        l, = struct.unpack("<i", aux[8: 12])
        assert len(aux) == 12 + l, "bad auxiliary"
        return archiver.unarchive(aux[12:])
    elif t == 3:
        n, = struct.unpack("<i", aux[8:12])
        return n
    elif t == 4:
        n, = struct.unpack("<q", aux[8:16])
        return n
    else:
        raise ValueError("unknown auxiliary type")


def pyobject_to_selector(s):
    return archiver.archive(s)


def selector_to_pyobject(sel):
    if not sel:
        return None
    return archiver.unarchive(sel)


if __name__ == '__main__':
    # from utils import hexdump
    # buf = open("dtx.dump", "rb").read() + b'\x00' * 64
    # sz = sizeof(DTXMessageHeader)
    # h0 = DTXMessageHeader.from_buffer_copy(buf[:sz])
    # print(h0.magic, h0.fragmentCount, h0.fragmentId, h0.length)
    # h1 = DTXMessageHeader.from_buffer_copy(buf[sz:sz + sz])
    # print(h1.magic, h1.fragmentCount, h1.fragmentId, h1.length)
    # buf=b'y[=\x1f \x00\x00\x00\x00\x00\x01\x00d\x02\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
    #     b'\x00\x00\x02\x00\x00\x00\xa9\x01\x00\x00T\x02\x00\x00\x00\x00\x00\x00\xf0\x01\x00\x00\x00\x00\x00\x00\x99' \
    #     b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x8d\x01\x00\x00bplist00\xd4\x01\x02\x03\x04\x05' \
    #     b'\x06\aX$versionY$archiverT$topX$objects\x12\x00\x01\x86\xa0_\x10\x0fNSKeyedArchiver\xd1\b\tTroot\x80\x01' \
    #     b'\xa7\v\f\x17\x18\x19\x1a\eU$null\xd3\r\x0e\x0f\x10\x13\x16WNS.keysZNS.objectsV$class\xa2\x11\x12\x80\x02' \
    #     b'\x80\x03\xa2\x14\x15\x80\x04\x80\x05\x80\x06_\x10\x1fcom.apple.private.DTXConnection_\x10%com.apple.private' \
    #     b'.DTXBlockCompression\x10\x01\x10\x02\xd2\x1c\x1d\x1e\x1fZ$classnameX$classes_\x10\x13NSMutableDictionary' \
    #     b'\xa3\x1e !\\NSDictionaryXNSObject\x00\b\x00\x11\x00\x1a\x00$\x00)\x002\x007\x00I\x00L\x00Q\x00S\x00[' \
    #     b'\x00a\x00h\x00p\x00{\x00\x82\x00\x85\x00\x87\x00\x89\x00\x8c\x00\x8e\x00\x90\x00\x92\x00\xb4\x00\xdc\x00' \
    #     b'\xde\x00\xe0\x00\xe5\x00\xf0\x00\xf9\x01\x0f\x01\x13\x01 ' \
    #     b'\x00\x00\x00\x00\x00\x00\x02\x01\x00\x00\x00\x00\x00\x00\x00\"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
    #     b'\x00\x00\x00\x01)bplist00\xd4\x01\x02\x03\x04\x05\x06\aX$versionY$archiverT$topX$objects\x12\x00\x01\x86' \
    #     b'\xa0_\x10\x0fNSKeyedArchiver\xd1\b\tTroot\x80\x01\xa2\v\fU$null_\x10\x1f_notifyOfPublishedCapabilities:\b' \
    #     b'\x11\x1a$)27ILQSV\\\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\r\x00\x00\x00\x00\x00\x00' \
    #     b'\x00\x00\x00\x00\x00\x00\x00\x00\x00~y[=\x1f ' \
    #     b'\x00\x00\x00\x00\x00\x01\x00\xa3\x01\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00' \
    #     b'\x00\x02\x10\x00\x00\xe4\x00\x00\x00\x93\x01\x00\x00\x00\x00\x00\x00\xf0\x01\x00\x00\x00\x00\x00\x00\xd4' \
    #     b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\xbc' \
    #     b'\x00\x00\x00bplist00\xd4\x01\x02\x03\x04\x05\x06\aX$versionY$archiverT$topX$objects\x12\x00\x01\x86\xa0_' \
    #     b'\x10\x0fNSKeyedArchiver\xd1\b\tTroot\x80\x01\xa2\v\fU$null_\x100com.apple.instruments.server.instrument_services' \
    #     b'.deviceinfo\b\x11\x1a$)27ILQSV\\\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\r\x00\x00\x00' \
    #     b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x8fbplist00\xd4\x01\x02\x03\x04\x05\x06' \
    #     b'\aX$versionY$archiverT$topX$objects\x12\x00\x01\x86\xa0_\x10\x0fNSKeyedArchiver\xd1\b\tTroot\x80\x01\xa2\v' \
    #     b'\fU$null_\x10#_requestChannelWithCode:identifier:\b\x11\x1a$)27ILQSV\\\x00\x00\x00\x00\x00\x00\x01\x01\x00' \
    #     b'\x00\x00\x00\x00\x00\x00\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x82'

    buf = b'y[=\x1f \x00\x00\x00\x00\x00\x01\x00\xa3\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\xe4\x00\x00\x00\x93\x01\x00\x00\x00\x00\x00\x00\xf0\x01\x00\x00\x00\x00\x00\x00\xd4\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x03\x00\x00\x00\x01\x00\x00\x00\n\x00\x00\x00\x02\x00\x00\x00\xbc\x00\x00\x00bplist00\xd4\x01\x02\x03\x04\x05\x06\x07\nY$archiverX$versionX$objectsT$top_\x10\x0fNSKeyedArchiver\x12\x00\x01\x86\xa0\xa2\x08\tU$null_\x100com.apple.instruments.server.instrument_services.deviceinfo\xd1\x0b\x0cTroot\x80\x01\x08\x11\x1b$-2DILR\x85\x88\x8d\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x8fbplist00\xd4\x01\x02\x03\x04\x05\x06\x07\nY$archiverX$versionX$objectsT$top_\x10\x0fNSKeyedArchiver\x12\x00\x01\x86\xa0\xa2\x08\tU$null_\x10#_requestChannelWithCode:identifier:\xd1\x0b\x0cTroot\x80\x01\x08\x11\x1b$-2DILRx{\x80\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x82'

    # hexdump(buf[:100])
    # hexdump(buf[h1.length + sz + sz:][:100])
    p = DTXMessage.from_bytes(buf)

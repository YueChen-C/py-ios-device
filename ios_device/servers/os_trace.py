#!/usr/bin/env python3
# Referenced from
# https://github.com/doronz88/pymobiledevice3/blob/5003eb82b45a3da9ef2c472c88361ec454497469/pymobiledevice3/services/os_trace.py
import logging
import plistlib
import struct
from abc import ABC
from datetime import datetime

from construct import Struct, Bytes, Int32ul, CString, Optional, Enum, Byte, Adapter, Int16ul, this, Computed

from ios_device.util.lockdown import LockdownClient

CHUNK_SIZE = 4096
TIME_FORMAT = '%H:%M:%S'
SYSLOG_LINE_SPLITTER = '\n\x00'


class TimestampAdapter(Adapter, ABC):
    def _decode(self, obj, context, path):
        return datetime.fromtimestamp(obj.seconds + (obj.microseconds / 1000000))

    def _encode(self, obj, context, path):
        return list(map(int, obj.split(".")))


timestamp_t = Struct(
    'seconds' / Int32ul,
    Bytes(4),
    'microseconds' / Int32ul
)


def try_decode(s):
    try:
        return s.decode('utf8')
    except UnicodeDecodeError:
        return s


syslog_t = Struct(
    Bytes(9),
    'pid' / Int32ul,
    Bytes(42),
    'timestamp' / TimestampAdapter(timestamp_t),
    Bytes(1),
    'level' / Enum(Byte, Notice=0, Info=0x01, Debug=0x02, Error=0x10, Fault=0x11),
    Bytes(38),
    'image_name_size' / Int16ul,
    'message_size' / Int16ul,
    Bytes(19),
    'filename' / CString('utf8'),
    '_image_name' / Bytes(this.image_name_size),
    'image_name' / Computed(lambda ctx: try_decode(ctx._image_name[:-1])),
    '_message' / Bytes(this.message_size),
    'message' / Computed(lambda ctx: try_decode(ctx._message[:-1])),
    'label' / Optional(Struct(
        'bundle_id' / CString('utf8'),
        'identifier' / CString('utf8')
    )),
)


class OsTraceService(object):
    SERVICE_NAME = 'com.apple.os_trace_relay'

    def __init__(self, lockdown: LockdownClient=None):
        self.logger = logging.getLogger(__name__)
        self.lockdown = lockdown if lockdown else LockdownClient()
        self.c = self.lockdown.start_service(self.SERVICE_NAME)

    def get_pid_list(self):
        self.c.send_plist({'Request': 'PidList'})
        self.c.recv_exact(1)
        return self.c.recv_plist()

    def syslog(self, pid=-1):
        self.c.send_plist({'Request': 'StartActivity', 'MessageFilter': 65535, 'Pid': pid, 'StreamFlags': 60})

        length_length, = struct.unpack('<I', self.c.recv_exact(4))
        length = int(self.c.recv_exact(length_length)[::-1].hex(), 16)
        print("length_length",length)
        response = plistlib.loads(self.c.recv_exact(length))

        if response.get('Status') != 'RequestSuccessful':
            raise Exception(f'got invalid response: {response}')

        while True:
            self.c.recv_exact(1)
            length, = struct.unpack('<I', self.c.recv_exact(4))
            line = self.c.recv(length)
            entry = syslog_t.parse(line)
            yield entry


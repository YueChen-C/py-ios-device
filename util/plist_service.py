"""
Plist Service - handles parsing and formatting plist content
"""

import logging
import plistlib
import re
import ssl
import struct
from socket import socket
from typing import Optional, Dict, Any

from .usbmux import USBMux, MuxDevice

__all__ = ['PlistService']
log = logging.getLogger(__name__)
HARDWARE_PLATFORM_SUB = re.compile(r'[^\w<>/ \-_0-9\"\'\\=.?!+]+').sub


class PlistService:
    def __init__(
            self,
            port: int,
            udid: Optional[str] = None,
            device: Optional[MuxDevice] = None,
            ssl_file: Optional[str] = None,
    ):
        self.port = port
        self.device = device or USBMux().find_device(udid, 0.1)
        log.debug(f'Connecting to device: {self.device.serial}')
        self.sock = self.device.connect(port)  # type: socket
        if ssl_file:
            self.ssl_start(ssl_file, ssl_file)

    def ssl_start(self, keyfile, certfile):
        self.sock = ssl.wrap_socket(self.sock, keyfile, certfile, ssl_version=ssl.PROTOCOL_TLSv1)

    def recv(self, length=4096):
        return self.sock.recv(length)

    def close(self):
        self.sock.close()

    def recv_exact(self, to_read) -> bytes:
        buffer = bytearray(to_read)
        view = memoryview(buffer)
        while view:
            if received := self.sock.recv_into(view, to_read):
                view = view[received:]
                to_read -= received
            else:
                break
        return buffer

    def recv_plist(self) -> Optional[Dict[str, Any]]:
        resp = self.recv_exact(4)
        if not resp or len(resp) != 4:
            return None
        if not (payload := self.recv_exact(struct.unpack('>L', resp)[0])):
            return None

        if payload.startswith(b'bplist00'):
            return plistlib.loads(payload)
        elif payload.startswith(b'<?xml'):
            # HAX lockdown HardwarePlatform with null bytes
            payload = HARDWARE_PLATFORM_SUB('', payload.decode('utf-8')).encode('utf-8')
            return plistlib.loads(payload)
        else:
            raise ValueError('Received invalid data: {}'.format(payload[:100].decode('hex')))

    def send_plist(self, d):
        payload = plistlib.dumps(d)
        payload_len = struct.pack('>L', len(payload))
        return self.sock.send(payload_len + payload)

    def plist_request(self, request):
        self.send_plist(request)
        return self.recv_plist()

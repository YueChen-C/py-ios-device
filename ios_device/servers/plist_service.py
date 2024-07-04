"""
Plist Service - handles parsing and formatting plist content
"""
import plistlib
import re
import socket
import ssl
import struct
from typing import Optional, Dict, Any
from ios_device.util import Log
from ios_device.util.exceptions import MuxError
from ios_device.util.usbmux import USBMux

__all__ = ['PlistService']

from ios_device.util.utils import set_keepalive

log = Log.getLogger(__name__)
HARDWARE_PLATFORM_SUB = re.compile(r'[^\w<>/ \-_0-9\"\'\\=.?!+]+').sub


class PlistService:
    def __exit__(self, *args):
        self.close()

    def __init__(self, sock, device=None):
        self.sock = sock
        self.device = device

    @staticmethod
    def create_tcp(hostname: str, port: int, keep_alive: bool = True):
        sock = socket.create_connection((hostname, port))
        if keep_alive:
            set_keepalive(sock)
        return PlistService(sock)

    @staticmethod
    def create_usbmux(port: int, udid: Optional[str], network=None, ssl_file=None):
        with USBMux() as usb_mux:
            device = usb_mux.find_device(udid, network)
        sock = device.connect(port)  # type: socket
        server = PlistService(sock, device)
        if ssl_file:
            server.ssl_start(ssl_file, ssl_file)
        return server

    def ssl_start(self, keyfile, certfile):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.load_cert_chain(keyfile=keyfile, certfile=certfile)
        self.sock = context.wrap_socket(self.sock)

    def send(self, msg):
        total_sent = 0
        while total_sent < len(msg):
            sent = self.sock.send(msg[total_sent:])
            if sent == 0:
                raise MuxError('socket connection broken')
            total_sent = total_sent + sent

    def recv(self, length=4096, timeout=-1):
        try:
            if timeout > 0:
                self.sock.settimeout(timeout)
            buf = self.sock.recv(length)
            return buf
        except Exception as E:
            return b''

    def close(self):
        self.sock.close()

    def recv_exact(self, to_read) -> bytes:
        buffer = bytearray(to_read)
        view = memoryview(buffer)
        while view:
            received = self.sock.recv_into(view, to_read)
            if received:
                view = view[received:]
                to_read -= received
            else:
                break
        return buffer

    def recv_plist(self) -> Optional[Dict[str, Any]]:
        resp = self.recv_exact(4)
        if not resp or len(resp) != 4:
            return None
        payload = self.recv_exact(struct.unpack('>L', resp)[0])
        log.debug(f'接收 Plist byte: {payload}')

        if not payload:
            return None
        if payload.startswith(b'bplist00') or payload.startswith(b'<?xml'):
            data = plistlib.loads(payload)
            log.debug(f'接收 Plist data: {data}')
            return data
        else:
            raise ValueError('Received invalid data: {}'.format(payload[:100].decode('hex')))

    def send_plist(self, data):
        log.debug(f'发送 Plist: {data}')
        payload = plistlib.dumps(data)
        payload_len = struct.pack('>L', len(payload))
        log.debug(f'发送 Plist byte: {payload_len + payload}')
        return self.sock.send(payload_len + payload)

    def plist_request(self, request):
        self.send_plist(request)
        return self.recv_plist()

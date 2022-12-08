#!/usr/bin/env python3

import logging
import struct

from construct import Struct, Int32ub, Int32ul, Bytes, Byte, this, Padding, Padded, CString

from ios_device.util.lockdown import LockdownClient

packet_struct = Struct(
    'hdr_len' / Int32ub,
    'hdr_version' / Byte,
    'payload_len' / Int32ub,
    'if_type' / Byte,
    'if_unit' / Padding(2),
    'in_out' / Padding(1),
    'proto_family' / Int32ub,
    'pre_len' / Int32ub,
    'post_len' / Int32ub,
    'interface_name' / Padded(16, CString('utf8')),
    'pid' / Int32ul,
    'comm' / Padded(17, CString('utf8')),
    'svc_class' / Int32ub,
    'epid' / Int32ul,
    'ecomm' / Padded(17, CString('utf8')),
    'epoch_seconds' / Int32ub,
    'epoch_microseconds' / Int32ub,
)


class PcapdService(object):
    IN_OUT_MAP = {0x01: 'O', 0x10: 'I'}
    SERVICE_NAME = "com.apple.pcapd"

    def __init__(self, lockdown=None, udid=None, network=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown or LockdownClient(udid=udid, network=network)
        self.conn = self.lockdown.start_service(self.SERVICE_NAME)

    def __iter__(self):

        ctp = self._chunk_to_packet

        while True:
            chunk = self.conn.recv_plist()
            yield ctp(chunk)

    def _chunk_to_packet(self, chunk):
        packet = packet_struct.parse(chunk)
        packet.payload = chunk[packet.hdr_len:]

        if not (packet.hdr_version == 2 and len(packet.payload) == packet.payload_len):
            raise ValueError('unsupported version')
        packet.epoch_microseconds = packet.epoch_seconds * 1000000 + packet.epoch_microseconds
        if packet.if_type == 0xFF:
            packet.is_eth = False  # cellular
            packet.payload = packet.payload[4:]
        elif packet.if_type == 0x06:
            packet.is_eth = True  # wifi
        else:
            raise ValueError('unknown link type {}'.format(hex(packet.if_type)))

        return packet


class PCAPPacketDumper:
    HEADER_STRUCT = struct.Struct('=IHHiIII')
    PACKET_STRUCT = struct.Struct('=IIII')

    def __init__(self, pkt_iter, out_file):
        self.pkt_iter = pkt_iter
        self.out_file = out_file

    def run(self, packet_cb=None):
        self.out_file.write(self.HEADER_STRUCT.pack(0xa1b2c3d4, 2, 4, 0, 0, 0xFFFFFFFF, 1))
        for pkt in self.pkt_iter:
            packet_cb is not None and packet_cb(pkt)
            payload = pkt.payload
            if not pkt.is_eth:
                if pkt.proto_family == 2:
                    ether_type_b = b'\x08\x00'  # IPv4
                elif pkt.proto_family == 30:
                    ether_type_b = b'\x86\xDD'  # IPv6
                else:
                    raise NotImplementedError('unsupported proto family {}'.format(pkt.proto_family))
                payload = b''.join((bytes(12), ether_type_b, payload))
            header = self.PACKET_STRUCT.pack(pkt.epoch_microseconds // 1000000,
                                             pkt.epoch_microseconds % 1000000,
                                             len(payload), len(payload))
            self.out_file.writelines((header, payload))

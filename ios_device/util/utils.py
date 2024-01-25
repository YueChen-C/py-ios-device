"""
Utils
"""
import asyncio
import math
import os
import platform
import socket
import struct
import traceback
import uuid

from functools import wraps

from typing import Callable

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

_NotSet = object()
NANO_SECOND = 1e9  # ns
MOVIE_FRAME_COST = 1 / 24

DEFAULT_AFTER_IDLE_SEC = 3
DEFAULT_INTERVAL_SEC = 3
DEFAULT_MAX_FAILS = 3

_DARWIN_TCP_KEEPALIVE = 0x10
_DARWIN_TCP_KEEPINTVL = 0x101
_DARWIN_TCP_KEEPCNT = 0x102


class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


class DictAttrProperty:
    def __init__(self, attr, path, type=_NotSet, default=_NotSet, default_factory=_NotSet, delim='.'):
        """
        Descriptor that acts as a cached property for retrieving values nested in a dict stored in an attribute of the
        object that this :class:`DictAttrProperty` is a member of.  The value is not accessed or stored until the first
        time that it is accessed.

        As an instance attribute of a subclass of :class:`DictAttrPropertyMixin` (or any class that has
        :class:`DictAttrPropertyMeta` as its metaclass), replaces itself with the value found at the given key in that
        instance's provided attribute.  Without :class:`DictAttrPropertyMeta` as its metaclass, the value is re-computed
        each time it is accessed.

        To un-cache a value (causes the descriptor to take over again)::\n
            # >>> del instance.__dict__[attr_name]

        The :class:`ClearableCachedPropertyMixin` mixin class can be used to facilitate clearing all
        :class:`DictAttrProperty` and any similar cached properties that exist in a given object.

        :param str attr: Name of the attribute in the class that this DictAttrProperty is in that contains the dict that
          This DictAttrProperty should reference
        :param str path: The nexted key location in the dict attribute of the value that this DictAttrProperty
          represents; dict keys should be separated by ``.``, otherwise the delimiter should be provided via ``delim``
        :param callable type: Callable that accepts 1 argument; the value of this DictAttrProperty will be passed to it,
          and the result will be returned as this DictAttrProperty's value (default: no conversion)
        :param default: Default value to return if a KeyError is encountered while accessing the given path
        :param callable default_factory: Callable that accepts no arguments to be used to generate default values
          instead of an explicit default value
        :param str delim: Separator that was used between keys in the provided path (default: ``.``)
        """
        self.path = [p for p in path.split(delim) if p]
        self.path_repr = delim.join(self.path)
        self.attr = attr
        self.type = type
        self.name = '_{}#{}'.format(self.__class__.__name__, self.path_repr)
        self.default = default
        self.default_factory = default_factory

    def __set_name__(self, owner, name):
        self.name = name
        path = ''.join('[{!r}]'.format(p) for p in self.path)
        self.__doc__ = (
            "A :class:`DictAttrProperty<pypod.idevice.utils.DictAttrProperty>` that references"
            f" this {owner.__name__} instance's {self.attr}{path}"
        )

    def __get__(self, obj, cls):
        if obj is None:
            return self

        value = getattr(obj, self.attr)
        for key in self.path:
            try:
                value = value[key]
            except KeyError:
                if self.default is not _NotSet:
                    value = self.default
                    break
                elif self.default_factory is not _NotSet:
                    value = self.default_factory()
                    break
                raise DictAttrFieldNotFoundError(obj, self.name, self.attr, self.path_repr)

        if self.type is not _NotSet:
            # noinspection PyArgumentList
            value = self.type(value)
        if '#' not in self.name:
            obj.__dict__[self.name] = value
        return value


class DictAttrFieldNotFoundError(Exception):
    def __init__(self, obj, prop_name, attr, path_repr):
        self.obj = obj
        self.prop_name = prop_name
        self.attr = attr
        self.path_repr = path_repr

    def __str__(self):
        fmt = '{!r} object has no attribute {!r} ({} not found in {!r}.{})'
        return fmt.format(type(self.obj).__name__, self.prop_name, self.path_repr, self.obj, self.attr)


def kperf_data(messages):
    _list = []
    p_record = 0
    m_len = len(messages)
    if m_len % 64 != 0:
        return _list
    while p_record < m_len:
        _list.append(struct.unpack('<QLLQQQQLLQ', messages[p_record:p_record + 64]))
        p_record += 64
    return _list


def convertBytes(_bytes):
    lst = ['Bytes', 'KiB', 'MiB', 'GiB', 'TiB']
    i = 0
    if isinstance(_bytes, int) and (_bytes > 0):
        i = int(math.floor(  # 舍弃小数点，取小
            math.log(_bytes, 1024)  # 求对数(对数：若 a**b = N 则 b 叫做以 a 为底 N 的对数)
        ))
    if i >= len(lst):
        i = len(lst) - 1
    return ('%.2f' + " " + lst[i]) % (_bytes / math.pow(1024, i))


class DumpDisk:

    def __init__(self):
        self.last_diskBytesRead = 1e100
        self.last_diskBytesWritten = 1e100
        self.last_diskReadOps = 0
        self.last_diskWriteOps = 0
        self.filter = ["Data Read", "Data Read/sec", "Data Written", "Data Written/sec", "Reads in", "Reads in/sec",
                       "Writes Out", "Writes Out/sec"]

    def decode(self, System):
        diskBytesRead = System.get('diskBytesRead')
        diskBytesRead_str = f"{convertBytes(diskBytesRead)}"
        diskBytesRead_qps = f"{convertBytes(diskBytesRead - self.last_diskBytesRead)}" if diskBytesRead - self.last_diskBytesRead > 0 else 0
        self.last_diskBytesRead = diskBytesRead

        diskBytesWritten = System.get('diskBytesWritten')

        diskBytesWritten_str = f"{convertBytes(diskBytesWritten)}"
        diskBytesWritten_qps = f"{convertBytes(diskBytesWritten - self.last_diskBytesWritten)}" if diskBytesWritten - self.last_diskBytesWritten > 0 else 0
        self.last_diskBytesWritten = diskBytesWritten

        diskReadOps = System.get('diskReadOps')
        diskReadOps_sec = diskReadOps - self.last_diskReadOps if diskReadOps - self.last_diskReadOps > 0 else 0
        self.last_diskReadOps = diskReadOps
        diskWriteOps = System.get('diskWriteOps')

        diskWriteOps_sec = diskWriteOps - self.last_diskWriteOps if diskWriteOps - self.last_diskWriteOps > 0 else 0
        self.last_diskWriteOps = diskWriteOps
        disk = [diskBytesRead_str, diskBytesRead_qps, diskBytesWritten_str, diskBytesWritten_qps, diskReadOps,
                diskReadOps_sec, diskWriteOps, diskWriteOps_sec]
        return dict(zip(self.filter, disk))


class DumpNetwork:

    def __init__(self):
        self.last_netBytesIn = 1e100
        self.last_netBytesOut = 1e100
        self.last_netPacketsIn = 0
        self.last_netPacketsOut = 0
        self.filter = ["Data Received", "Data Received/sec", "Data Sent", "Data Sent/sec", "Packets in",
                       "Packets in/sec",
                       "Packets Out", "Packets Out/sec"]

    def decode(self, System):
        netBytesIn = System.get('netBytesIn')
        netBytesIn_str = f"{convertBytes(netBytesIn)}"
        netBytesIn_qps = f"{convertBytes(netBytesIn - self.last_netBytesIn)}" if netBytesIn - self.last_netBytesIn > 0 else 0
        self.last_netBytesIn = netBytesIn

        netBytesOut = System.get('netBytesOut')

        netBytesOut_str = f"{convertBytes(netBytesOut)}"
        netBytesOut_qps = f"{convertBytes(netBytesOut - self.last_netBytesOut)}" if netBytesOut - self.last_netBytesOut > 0 else 0
        self.last_netBytesOut = netBytesOut

        netPacketsIn = System.get('netPacketsIn')
        netPacketsIn_sec = netPacketsIn - self.last_netPacketsIn if netPacketsIn - self.last_netPacketsIn > 0 else 0
        self.last_netPacketsIn = netPacketsIn

        netPacketsOut = System.get('netPacketsOut')
        disk_write_ops_sec = netPacketsOut - self.last_netPacketsOut if netPacketsOut - self.last_netPacketsOut > 0 else 0
        self.last_netPacketsOut = netPacketsOut

        data = [netBytesIn_str, netBytesIn_qps, netBytesOut_str, netBytesOut_qps, netPacketsOut,
                netPacketsIn_sec, netPacketsOut, disk_write_ops_sec]
        return dict(zip(self.filter, data))


class DumpMemory:

    def __init__(self):
        self.kernel_page_size = 16384  # core_profile_session_tap get kernel_page_size

    def decode(self, system: dict):
        app_memory = convertBytes(
            (system.get('vmIntPageCount') - system.get("vmPurgeableCount")) * self.kernel_page_size)
        cached_files = convertBytes(
            (system.get('vmExtPageCount') + system.get("vmPurgeableCount")) * self.kernel_page_size)
        compressed = convertBytes(system.get('vmCompressorPageCount') * self.kernel_page_size)
        memory_used = convertBytes((system.get('vmUsedCount') - system.get('vmExtPageCount')) * self.kernel_page_size)
        wired_memory = convertBytes(system.get("vmWireCount") * self.kernel_page_size)
        swap_used = convertBytes(system.get("__vmSwapUsage"))
        free_memory = convertBytes(system.get("vmFreeCount") * self.kernel_page_size)
        data = {"App Memory": app_memory, "Free Memory": free_memory, "Cached Files": cached_files,
                "Compressed": compressed,
                "Memory Used": memory_used, "Wired Memory": wired_memory, "Swap Used": swap_used}
        return data


def set_keepalive(sock: socket.socket, after_idle_sec: int = DEFAULT_AFTER_IDLE_SEC,
                  interval_sec: int = DEFAULT_INTERVAL_SEC, max_fails: int = DEFAULT_MAX_FAILS) -> None:
    """
    set keep-alive parameters on a given socket

    :param sock: socket to operate on
    :param after_idle_sec: idle time used when SO_KEEPALIVE is enabled
    :param interval_sec: interval between keepalives
    :param max_fails: number of keepalives before close

    """
    plat = platform.system()
    if plat == 'Linux':
        return _set_keepalive_linux(sock, after_idle_sec, interval_sec, max_fails)
    if plat == 'Darwin':
        return _set_keepalive_darwin(sock, after_idle_sec, interval_sec, max_fails)
    if plat == 'Windows':
        return _set_keepalive_win(sock, after_idle_sec, interval_sec)
    raise RuntimeError(f'Unsupported platform {plat}')


def _set_keepalive_linux(sock: socket.socket, after_idle_sec: int = DEFAULT_AFTER_IDLE_SEC,
                         interval_sec: int = DEFAULT_INTERVAL_SEC, max_fails: int = DEFAULT_MAX_FAILS) -> None:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)


def _set_keepalive_darwin(sock: socket.socket, after_idle_sec: int = DEFAULT_AFTER_IDLE_SEC,
                          interval_sec: int = DEFAULT_INTERVAL_SEC, max_fails: int = DEFAULT_MAX_FAILS) -> None:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, _DARWIN_TCP_KEEPALIVE, after_idle_sec)
    sock.setsockopt(socket.IPPROTO_TCP, _DARWIN_TCP_KEEPINTVL, interval_sec)
    sock.setsockopt(socket.IPPROTO_TCP, _DARWIN_TCP_KEEPCNT, max_fails)


def _set_keepalive_win(sock: socket.socket, after_idle_sec: int = DEFAULT_AFTER_IDLE_SEC,
                       interval_sec: int = DEFAULT_INTERVAL_SEC) -> None:
    sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, after_idle_sec * 1000, interval_sec * 1000))


def get_host_id():
    return str(uuid.uuid3(uuid.NAMESPACE_DNS, platform.node())).upper()
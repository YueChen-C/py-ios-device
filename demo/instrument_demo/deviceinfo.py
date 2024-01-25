"""
获取系统信息
"""
import os
import sys

from ios_device.remote.remote_lockdown import RemoteLockdownClient

sys.path.append(os.getcwd())
from ios_device.servers.Instrument import InstrumentServer
from ios_device.util import logging

log = logging.getLogger(__name__)


def runningProcesses(rpc):
    """ 获取所有运行的进程信息
    :param rpc:
    :return:
    """
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "runningProcesses").selector
    log.debug("runningProcesses:")
    headers = '\t'.join(sorted(parsed[0].keys()))
    log.debug(headers)
    for item in parsed:
        sorted_item = sorted(item.items())
        print('\t'.join(map(str, [v for _, v in sorted_item])))
    rpc.stop()
    return parsed


def execnameForPid(rpc, pid):
    """ 获取 pid 进程的应用名
    :param rpc:
    :param pid:
    :return:
    """
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "execnameForPid:", str(pid)).selector
    print(parsed)
    rpc.stop()
    return parsed


def machTimeInfo(rpc):
    machTimeInfo = rpc.call("com.apple.instruments.server.services.deviceinfo", "machTimeInfo").selector
    print(machTimeInfo)
    rpc.stop()
    return machTimeInfo


def traceCodesFile(rpc):
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "traceCodesFile").selector
    print(parsed)
    rpc.stop()
    return parsed


def networkInformation(rpc):
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "networkInformation").selector
    print(parsed)
    rpc.stop()


def systemInformation(rpc):
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "systemInformation").selector
    print(parsed)
    rpc.stop()


def sysmonProcessAttributes(rpc):
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "sysmonProcessAttributes").selector
    print(parsed)
    rpc.stop()


def sysmonSystemAttributes(rpc):
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "symbolicatorSignaturesForExpiredPids").selector
    print(list(parsed))
    rpc.stop()


if __name__ == '__main__':
    host = 'fd73:3a0d:d4bd::1'  # randomized
    port = 60558  # randomized
    with RemoteLockdownClient((host, port)) as rsd:
        rpc = InstrumentServer(rsd).init()
        sysmonProcessAttributes(rpc)
        rpc.stop()

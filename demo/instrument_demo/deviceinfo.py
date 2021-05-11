"""
获取系统信息
"""
import os
import sys

sys.path.append(os.getcwd())
from ios_device.servers.Instrument import InstrumentServer
from ios_device.util import logging

log = logging.getLogger(__name__)


def runningProcesses(rpc):
    """ 获取所有运行的进程信息
    :param rpc:
    :return:
    """
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "runningProcesses").parsed
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
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "execnameForPid:", str(pid)).parsed
    print(parsed)
    rpc.stop()
    return parsed


def machTimeInfo(rpc):
    machTimeInfo = rpc.call("com.apple.instruments.server.services.deviceinfo", "machTimeInfo").parsed
    print(machTimeInfo)
    rpc.stop()
    return machTimeInfo


def traceCodesFile(rpc):
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "traceCodesFile").parsed
    print(parsed)
    rpc.stop()
    return parsed


def networkInformation(rpc):
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "networkInformation").parsed
    print(parsed)
    rpc.stop()


def systemInformation(rpc):
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "systemInformation").parsed
    print(parsed)
    rpc.stop()


def sysmonProcessAttributes(rpc):
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "sysmonProcessAttributes").parsed
    print(parsed)
    rpc.stop()


def sysmonSystemAttributes(rpc):
    parsed = rpc.call("com.apple.instruments.server.services.deviceinfo", "symbolicatorSignaturesForExpiredPids").parsed
    print(list(parsed))
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    runningProcesses(rpc)
    rpc.stop()

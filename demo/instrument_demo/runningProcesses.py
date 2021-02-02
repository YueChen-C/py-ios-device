"""
查看所有正在运行的进程信息
"""
import os
import sys

sys.path.append(os.getcwd())
from ios_device.servers.Instrument import InstrumentServer
from ios_device.util import logging

log = logging.getLogger(__name__)


def runningProcesses(rpc):
    running = rpc.call("com.apple.instruments.server.services.deviceinfo", "runningProcesses").parsed
    log.debug("runningProcesses:")
    headers = '\t'.join(sorted(running[0].keys()))
    log.debug(headers)
    for item in running:
        sorted_item = sorted(item.items())
        print('\t'.join(map(str, [v for _, v in sorted_item])))
    rpc.stop()
    return running


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    runningProcesses(rpc)
    rpc.deinit()

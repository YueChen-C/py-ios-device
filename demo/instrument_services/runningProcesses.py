"""
查看所有正在运行的进程信息
"""
import os
import sys

sys.path.append(os.getcwd())
from instrument.RPC import get_usb_rpc
from util import logging

log = logging.getLogger(__name__)


def runningProcesses(rpc):
    rpc.start()
    running = rpc.call("com.apple.instruments.server.services.deviceinfo", "runningProcesses").parsed
    log.debug("runningProcesses:")
    headers = '\t'.join(sorted(running[0].keys()))
    log.debug(headers)
    for item in running:
        sorted_item = sorted(item.items())
        log.debug('\t'.join(map(str, [v for _, v in sorted_item])))
    rpc.stop()
    return running


if __name__ == '__main__':
    rpc = get_usb_rpc()
    runningProcesses(rpc)
    rpc.deinit()

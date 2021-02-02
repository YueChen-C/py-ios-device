"""
获取系统相关信息，类似 Android TOP，包含进程信息，需要 iOS > 11
"""
import os
import sys

from ios_device.servers.Instrument import InstrumentServer

sys.path.append(os.getcwd())
import json
import time
from ios_device.util import logging

log = logging.getLogger(__name__)


def sysmontap(rpc):

    def dropped_message(res):
        print("[DROP]", res.parsed, res.raw.channel_code)

    def on_sysmontap_message(res):

        if isinstance(res.parsed, list):
            print(json.dumps(res.parsed, indent=4))
    rpc.register_unhandled_callback(dropped_message)
    rpc.call("com.apple.instruments.server.services.sysmontap", "setConfig:", {
        'ur': 1000,  # 输出频率 ms
        'bm': 0,
        'procAttrs': ['memVirtualSize', 'cpuUsage', 'procStatus', 'appSleep', 'uid', 'vmPageIns', 'memRShrd',
                      'ctxSwitch', 'memCompressed', 'intWakeups', 'cpuTotalSystem', 'responsiblePID', 'physFootprint',
                      'cpuTotalUser', 'sysCallsUnix', 'memResidentSize', 'sysCallsMach', 'memPurgeable',
                      'diskBytesRead', 'machPortCount', '__suddenTerm', '__arch', 'memRPrvt', 'msgSent', 'ppid',
                      'threadCount', 'memAnon', 'diskBytesWritten', 'pgid', 'faults', 'msgRecv', '__restricted', 'pid',
                      '__sandbox'],  # 输出所有进程信息字段，字段顺序与自定义相同（全量自字段，按需使用）
        'sysAttrs': ['diskWriteOps', 'diskBytesRead', 'diskBytesWritten', 'threadCount', 'vmCompressorPageCount',
                     'vmExtPageCount', 'vmFreeCount', 'vmIntPageCount', 'vmPurgeableCount', 'netPacketsIn',
                     'vmWireCount', 'netBytesIn', 'netPacketsOut', 'diskReadOps', 'vmUsedCount', '__vmSwapUsage',
                     'netBytesOut'],  # 系统信息字段
        'cpuUsage': True,
        'sampleInterval': 1000000000})
    rpc.register_channel_callback("com.apple.instruments.server.services.sysmontap", on_sysmontap_message)
    var = rpc.call("com.apple.instruments.server.services.sysmontap", "start").parsed
    print(f"start {var}")
    time.sleep(10)
    var = rpc.call("com.apple.instruments.server.services.sysmontap", "stop").parsed
    print(f"stop {var}")
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    sysmontap(rpc)
    rpc.deinit()

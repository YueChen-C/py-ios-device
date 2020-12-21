"""
获取系统相关信息，类似 Android TOP，包含进程信息，需要 iOS > 11
"""
import os
import sys

sys.path.append(os.getcwd())
import json
import time
from threading import Event
from instrument import RPC
from util import logging

log = logging.getLogger(__name__)

def sysmontap(rpc):
    done = Event()

    def _notifyOfPublishedCapabilities(res):
        done.set()

    def dropped_message(res):
        log.debug("[DROP]", res.parsed, res.raw.channel_code)

    def on_sysmontap_message(res):
        if isinstance(res.parsed, list):
            log.debug(json.dumps(res.parsed, indent=4))

    rpc.register_callback("_notifyOfPublishedCapabilities:", _notifyOfPublishedCapabilities)
    rpc.register_unhandled_callback(dropped_message)
    rpc.start()
    if not done.wait(5):
        log.debug("[WARN] timeout waiting capabilities")
    rpc.call("com.apple.instruments.server.services.sysmontap", "setConfig:", {
        'ur': 1000,  # 输出频率 ms
        'procAttrs': ['pid', 'memVirtualSize', 'cpuUsage', 'ctxSwitch', 'intWakeups', 'physFootprint',
                      'memResidentSize',
                      'memAnon', 'powerScore', 'diskBytesRead'],  # 输出所有进程信息，字段顺序与自定义相同
        'cpuUsage': True,
        'sampleInterval': 1000000000})
    rpc.register_channel_callback("com.apple.instruments.server.services.sysmontap", on_sysmontap_message)
    var = rpc.call("com.apple.instruments.server.services.sysmontap", "start").parsed
    print("start" + str(var))
    time.sleep(10)
    var = rpc.call("com.apple.instruments.server.services.sysmontap", "stop").parsed
    print("stop" + str(var))
    rpc.stop()


if __name__ == '__main__':
    rpc = RPC.get_usb_rpc()
    sysmontap(rpc)
    rpc.deinit()

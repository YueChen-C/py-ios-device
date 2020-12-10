"""
获取系统所有信息，包含进程信息
"""
import time
from threading import Event

from instrument.RPC import get_usb_rpc


def sysmontap(rpc):
    done = Event()

    def _notifyOfPublishedCapabilities(res):
        done.set()

    def dropped_message(res):
        print("[DROP]", res.parsed, res.raw.channel_code)

    def on_sysmontap_message(res):
        print("[SYSMONTAP]", res.parsed)

    rpc.register_callback("_notifyOfPublishedCapabilities:", _notifyOfPublishedCapabilities)
    rpc.register_unhandled_callback(dropped_message)
    rpc.start()
    if not done.wait(5):
        print("[WARN] timeout waiting capabilities")
    rpc.call("com.apple.instruments.server.services.sysmontap", "setConfig:", {
        'ur': 1000,
        'procAttrs': ['memVirtualSize', 'cpuUsage', 'ctxSwitch', 'intWakeups', 'physFootprint', 'memResidentSize',
                      'memAnon', 'pid', 'powerScore', 'diskBytesRead'],
        'bm': 0,
        'cpuUsage': True,
        'sampleInterval': 1000000000})  # 改这个也没反应
    rpc.register_channel_callback("com.apple.instruments.server.services.sysmontap", on_sysmontap_message)
    print("start", rpc.call("com.apple.instruments.server.services.sysmontap", "start").parsed)
    try:
        while 1: time.sleep(10)
    except:
        pass
    print("stop", rpc.call("com.apple.instruments.server.services.sysmontap", "stop").parsed)
    rpc.stop()


if __name__ == '__main__':
    rpc = get_usb_rpc()
    sysmontap(rpc)
    rpc.deinit()

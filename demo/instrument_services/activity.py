"""
获取单个应用 activity数据
"""
import time
import os
import sys

sys.path.append(os.getcwd())
from instrument.RPC import pre_call, get_usb_rpc
from util import logging

log = logging.getLogger(__name__)


def activity(rpc, pid, callback):
    def on_callback_message(res):
        log.debug("[ACTIVITY]", res.parsed)
        log.debug("\n")

    pre_call(rpc)
    # rpc.register_channel_callback("com.apple.instruments.server.services.activity", on_callback_message)
    rpc.register_channel_callback("com.apple.instruments.server.services.activity", callback)
    var = rpc.call("com.apple.instruments.server.services.activity", "startSamplingWithPid:", pid).parsed
    log.debug("start" + str(var))

    time.sleep(10)
    var = rpc.call("com.apple.instruments.server.services.activity", "stopSampling").parsed
    log.debug("stop" + str(var))
    rpc.stop()


if __name__ == '__main__':
    rpc = get_usb_rpc()
    activity(rpc, 31630)
    rpc.deinit()

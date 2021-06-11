"""
获取单个应用 activity数据
"""
import time
import os
import sys


sys.path.append(os.getcwd())
from ios_device.servers.Instrument import  InstrumentServer
from ios_device.util import logging

log = logging.getLogger(__name__)


def activity(rpc, pid):
    def on_callback_message(res):
        print(f"[ACTIVITY] {res.selector}", )
        print("\n")
    rpc.register_channel_callback("com.apple.instruments.server.services.activity", on_callback_message)
    var = rpc.call("com.apple.instruments.server.services.activity", "startSamplingWithPid:", pid).selector
    log.debug(f"start {var}")
    time.sleep(10)
    var = rpc.call("com.apple.instruments.server.services.activity", "stopSampling").selector
    log.debug(f"stop {var}")
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    activity(rpc, 261)
    rpc.stop()

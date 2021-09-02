"""
获取 gup 数据，返回时间序列还没琢磨出来怎么解析

startCollectingCounters 之后会返回参数详解之类的， 一些解析方式，但是看起来依然很费劲
"""
import os
import sys

from ios_device.util.dtx_msg import RawInt64sl

sys.path.append(os.getcwd())

from ios_device.servers.Instrument import InstrumentServer

import time
from ios_device.util import logging

log = logging.getLogger(__name__)


def gup(rpc):

    def dropped_message(res):
        print( res.selector,res.auxiliaries)


    # print(rpc.lockdown.device_id)
    rpc.register_undefined_callback(dropped_message)
    print(rpc.call('com.apple.instruments.server.services.deviceinfo','machTimeInfo').selector)
    print(rpc.call('com.apple.instruments.server.services.gpu','requestDeviceGPUInfo').selector)
    rpc.call("com.apple.instruments.server.services.gpu", "configureCounters:counterProfile:interval:windowLimit:tracingPID:",RawInt64sl(0, 3, 0, -1), 4294967295)
    print(rpc.call('com.apple.instruments.server.services.gpu', 'startCollectingCounters').selector)
    # rpc.call("com.apple.instruments.server.services.gpu", "")
    time.sleep(1000)

    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    gup(rpc)
    rpc.stop()

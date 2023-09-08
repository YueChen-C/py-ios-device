"""
获取 gpu 数据，返回时间序列还没琢磨出来怎么解析

正常情况下应该是 1000 组数据返回一次，每个设备都不同，也有可能是几万返回一次
"""
import os
import sys

from ios_device.util.dtx_msg import RawInt64sl, RawInt32sl
from ios_device.util.gpu_decode import GRCDecodeOrder, GRCDisplayOrder, JSEvn, TraceData

sys.path.append(os.getcwd())

from ios_device.servers.Instrument import InstrumentServer

import time
from ios_device.util import logging

log = logging.getLogger(__name__)


def gpu(rpc):
    decode_key_list = []
    js_env: JSEvn
    display_key_list = []

    def dropped_message(res):
        nonlocal js_env, decode_key_list, display_key_list
        if res.selector[0] == 1:
            js_env.dump_trace(TraceData(*res.selector[:6]))
        elif res.selector[0] == 0:
            # # print(res.selector)
            _data = res.selector[4]
            decode_key_list = GRCDecodeOrder.decode(_data.get(1))
            display_key_list = GRCDisplayOrder.decode(_data.get(0))
            js_env = JSEvn(_data.get(2), display_key_list, decode_key_list, mach_time_factor)

    rpc.register_undefined_callback(dropped_message)
    machTimeInfo = rpc.call("com.apple.instruments.server.services.deviceinfo", "machTimeInfo").selector
    mach_time_factor = machTimeInfo[1] / machTimeInfo[2]
    requestDeviceGPUInfo = rpc.call('com.apple.instruments.server.services.gpu', 'requestDeviceGPUInfo').selector

    min_collection_interval = requestDeviceGPUInfo[0].get('min-collection-interval')
    rpc.call("com.apple.instruments.server.services.gpu",
             "configureCounters:counterProfile:interval:windowLimit:tracingPID:",
             RawInt64sl(min_collection_interval, 3, 0, 0), RawInt32sl(-1))
    rpc.call('com.apple.instruments.server.services.gpu', 'startCollectingCounters')
    time.sleep(5)

    print(rpc.call('com.apple.instruments.server.services.gpu', 'stopCollectingCounters').selector)
    data = rpc.call('com.apple.instruments.server.services.gpu', 'flushRemainingData').selector
    js_env.dump_trace(TraceData(*data[0][:6]))
    time.sleep(2)
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    gpu(rpc)
    rpc.stop()

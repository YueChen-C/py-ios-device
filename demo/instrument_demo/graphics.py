"""
graphics 计算 fps
"""

import time
from ios_device.servers.Instrument import InstrumentServer


def cmd_graphics(rpc):
    last_timestamp = 0

    def dropped_message(res):
        print("[DROP]", res.selector, res.raw.channel_code)

    def on_graphics_message(res):
        data = res.selector
        nonlocal last_timestamp
        cost_time = data['XRVideoCardRunTimeStamp'] - last_timestamp
        last_timestamp = data['XRVideoCardRunTimeStamp']
        print(cost_time,'fps:', data['CoreAnimationFramesPerSecond'])

    rpc.register_undefined_callback(dropped_message)
    rpc.register_channel_callback("com.apple.instruments.server.services.graphics.opengl", on_graphics_message)
    print("start",
          rpc.call("com.apple.instruments.server.services.graphics.opengl", "startSamplingAtTimeInterval:", 0.0).selector)
    time.sleep(100)
    print("stop", rpc.call("com.apple.instruments.server.services.graphics.opengl", "stopSampling").selector)
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    cmd_graphics(rpc)
    rpc.stop()

import time
from threading import Event

from servers.Instrument import InstrumentServer


def cmd_graphics(rpc):
    done = Event()

    def _notifyOfPublishedCapabilities(res):
        done.set()

    def dropped_message(res):
        print("[DROP]", res.parsed, res.raw.channel_code)

    def on_graphics_message(res):
        print("[GRAPHICS]", res.parsed)

    rpc.register_callback("_notifyOfPublishedCapabilities:", _notifyOfPublishedCapabilities)
    rpc.register_unhandled_callback(dropped_message)
    rpc.start()
    if not done.wait(5):
        print("[WARN] timeout waiting capabilities")
    rpc.register_channel_callback("com.apple.instruments.server.services.graphics.opengl", on_graphics_message)
    print("set", rpc.call("com.apple.instruments.server.services.graphics.opengl", "setSamplingRate:",5.0).parsed)  # 5 -> 0.5秒一条消息
    # print("start",
          # rpc.call("com.apple.instruments.server.services.graphics.opengl", "startSamplingAtTimeInterval:", 0.0).parsed)
    print("start", rpc.call("com.apple.instruments.server.services.graphics.opengl", "startSamplingAtTimeInterval:processIdentifier:", 1, 0.0).parsed)
    try:
        while 1: time.sleep(10)
    except:
        pass
    print("stop", rpc.call("com.apple.instruments.server.services.graphics.opengl", "stopSampling").parsed)
    rpc.stop()

if __name__ == '__main__':
    rpc = InstrumentServer().init()
    cmd_graphics(rpc)
    rpc.deinit()

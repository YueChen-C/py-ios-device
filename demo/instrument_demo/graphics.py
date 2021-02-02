import time
from threading import Event

from ios_device.servers.Instrument import InstrumentServer


def cmd_graphics(rpc):
    def dropped_message(res):
        print("[DROP]", res.parsed, res.raw.channel_code)

    def on_graphics_message(res):
        print("[GRAPHICS]", res.parsed)

    rpc.register_unhandled_callback(dropped_message)
    rpc.register_channel_callback("com.apple.instruments.server.services.graphics.opengl", on_graphics_message)
    print("set", rpc.call("com.apple.instruments.server.services.graphics.opengl", "setSamplingRate:",
                          5.0).parsed)
    print("start", rpc.call("com.apple.instruments.server.services.graphics.opengl",
                            "startSamplingAtTimeInterval:processIdentifier:", 1, 0.0).parsed)
    time.sleep(10)
    print("stop", rpc.call("com.apple.instruments.server.services.graphics.opengl", "stopSampling").parsed)
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    cmd_graphics(rpc)
    rpc.deinit()

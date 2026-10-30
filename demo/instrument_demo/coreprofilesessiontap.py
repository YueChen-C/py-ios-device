import os
import sys
import time
import uuid

from ios_device.servers.Instrument import InstrumentServer
from ios_device.util.display_stats import FRAME_EVENT, DisplayStats
from ios_device.util.exceptions import InstrumentRPCParseError
from ios_device.util.kperf_data import kdbg_extract_all
from ios_device.util.utils import kperf_data

sys.path.append(os.getcwd())


def graphics_display(rpc):
    def dropped_message(res):
        print("[DROP]", res.selector, res.raw.channel_code)

    # mach tick -> 纳秒 的比值随设备不同，不能用固定值
    mach_time_info = rpc.call("com.apple.instruments.server.services.deviceinfo", "machTimeInfo").selector
    stats = DisplayStats(mach_time_info[1] / mach_time_info[2])

    def on_graphics_message(res):
        if type(res.selector) is not InstrumentRPCParseError:
            return
        for args in kperf_data(res.selector.data):
            if kdbg_extract_all(args[7]) == FRAME_EVENT:
                report = stats.add_frame(args[0])
                if report:
                    print(report)

    rpc.register_undefined_callback(dropped_message)
    rpc.register_channel_callback("com.apple.instruments.server.services.coreprofilesessiontap", on_graphics_message)
    print(
        "set",
        rpc.call(
            "com.apple.instruments.server.services.coreprofilesessiontap",
            "setConfig:",
            {
                "rp": 10,
                "tc": [{"kdf2": {630784000, 833617920, 830472456}, "tk": 3, "uuid": str(uuid.uuid4()).upper()}],
                "ur": 500,
            },
        ).selector,
    )
    print("start", rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "start").selector)
    time.sleep(10000)
    print("stop", rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "stop").selector)
    rpc.stop()


if __name__ == "__main__":
    # host = 'fd73:3a0d:d4bd::1'  # randomized
    # port = 60558  # randomized
    # with RemoteLockdownClient((host, port)) as rsd:
    #     rpc = InstrumentServer(rsd).init()
    #     graphics_display(rpc)
    #     rpc.stop()

    rpc = InstrumentServer().init()
    graphics_display(rpc)
    rpc.stop()

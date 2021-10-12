import os
import sys
import time
import uuid
from datetime import datetime


from ios_device.servers.Instrument import InstrumentServer
from ios_device.util.exceptions import InstrumentRPCParseError
from ios_device.util.kperf_data import KperfData
from ios_device.util.utils import kperf_data

sys.path.append(os.getcwd())

NANO_SECOND = 1e9  # ns
MOVIE_FRAME_COST = 1 / 24


def graphics_display(rpc):
    from numpy import mean
    from numpy.core import long

    def dropped_message(res):
        print("[DROP]", res.selector, res.raw.channel_code)

    last_frame = None
    last_1_frame_cost, last_2_frame_cost, last_3_frame_cost = 0, 0, 0
    jank_count = 0
    big_jank_count = 0
    jank_time_count = 0
    mach_time_factor = 125 / 3
    frame_count = 0
    time_count = 0
    last_time = datetime.now().timestamp()
    count_time = datetime.now().timestamp()
    _list = []

    def on_graphics_message(res):
        nonlocal frame_count, last_frame, last_1_frame_cost, last_2_frame_cost, last_3_frame_cost, time_count, mach_time_factor, last_time, \
            jank_count, big_jank_count, jank_time_count, _list, count_time
        if type(res.selector) is InstrumentRPCParseError:
            for args in kperf_data(res.selector.data):
                _time, code = args[0], args[7]
                if code == 830472984:
                    # time_count = 0
                    if not last_frame:
                        last_frame = long(_time)
                    else:
                        this_frame_cost = (long(_time) - last_frame) * mach_time_factor
                        if all([last_3_frame_cost != 0, last_2_frame_cost != 0, last_1_frame_cost != 0]):
                            if this_frame_cost > mean([last_3_frame_cost, last_2_frame_cost, last_1_frame_cost]) * 2 \
                                    and this_frame_cost > MOVIE_FRAME_COST * NANO_SECOND * 2:
                                jank_count += 1
                                jank_time_count += this_frame_cost
                                if this_frame_cost > mean(
                                        [last_3_frame_cost, last_2_frame_cost, last_1_frame_cost]) * 3 \
                                        and this_frame_cost > MOVIE_FRAME_COST * NANO_SECOND * 3:
                                    big_jank_count += 1

                        last_3_frame_cost, last_2_frame_cost, last_1_frame_cost = last_2_frame_cost, last_1_frame_cost, this_frame_cost
                        time_count += this_frame_cost
                        last_frame = long(_time)
                        frame_count += 1
                # else:
                #     time_count = (datetime.now().timestamp() - count_time) * NANO_SECOND
                    # print(time_count)

                if time_count > NANO_SECOND:
                    print(
                        f"{datetime.now().timestamp() - last_time} FPS: {frame_count / time_count * NANO_SECOND} jank: {jank_count} big_jank: {big_jank_count} stutter: {jank_time_count / time_count}")
                    jank_count = 0
                    big_jank_count = 0
                    jank_time_count = 0
                    frame_count = 0
                    time_count = 0
                    count_time = datetime.now().timestamp()

                # else:
                #     last_time = datetime.now().timestamp()

    rpc.register_undefined_callback(dropped_message)
    rpc.register_channel_callback("com.apple.instruments.server.services.coreprofilesessiontap", on_graphics_message)
    # 获取mach time比例
    Kperf = KperfData(rpc)

    machTimeInfo = rpc.call("com.apple.instruments.server.services.deviceinfo", "machTimeInfo").selector
    mach_time_factor = machTimeInfo[1] / machTimeInfo[2]

    print("set", rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "setConfig:",
                          {'rp': 10,
                           'tc': [{'kdf2': {630784000, 833617920, 830472456},
                                   'tk': 3,
                                   'uuid': str(uuid.uuid4()).upper()}],
                           'ur': 500}).selector)
    print("start",
          rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "start").selector)
    time.sleep(10000)
    print("stop", rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "stop").selector)
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    graphics_display(rpc)
    rpc.stop()

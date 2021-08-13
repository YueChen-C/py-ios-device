import os
import sys
import time
import uuid

from ios_device.cli.base import InstrumentDeviceInfo
from ios_device.servers.Instrument import InstrumentServer
from ios_device.util.exceptions import InstrumentRPCParseError
from ios_device.util.kperf_data import KdBufParser, KperfData

sys.path.append(os.getcwd())

NANO_SECOND = 1e9  # ns
MOVIE_FRAME_COST = 1 / 24


def graphics_display(rpc):

    def on_graphics_message(res):
        if type(res.selector) is InstrumentRPCParseError:
            for args in Kperf.to_str(res.selector.data):
                print(args)

    rpc.register_channel_callback("com.apple.instruments.server.services.coreprofilesessiontap", on_graphics_message)
    traceCodesFile = InstrumentDeviceInfo(rpc).traceCodesFile()
    Kperf = KperfData(traceCodesFile)
    rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "setConfig:",
             {
                 'tc': [{
                     'csd': 128,
                     'kdf2': {0xffffffff},
                     'ta': [[3], [0], [2], [1, 1, 0]],
                     'tk': 3,
                     'uuid': str(uuid.uuid4()),
                 }],
                 'rp': 100,
                 'bm': 0,
             })
    rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "start")
    time.sleep(10000)
    rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "stop")
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    graphics_display(rpc)
    rpc.stop()

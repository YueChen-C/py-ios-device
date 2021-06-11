import json
import time

from ios_device.servers.Instrument import InstrumentServer


def energy(rpc, pid):
    rpc._start()
    channel = "com.apple.xcode.debug-gauge-data-providers.Energy"
    attr = {}
    print("start", rpc.call(channel, "startSamplingForPIDs:", {pid}).selector)
    ret = rpc.call(channel, "sampleAttributes:forPIDs:", attr, {pid})
    print(ret.selector)
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    energy(rpc, 261)
    rpc.stop()

import os
import sys

from servers.Instrument import InstrumentServer
from util.dtxlib import auxiliary_to_pyobject

sys.path.append(os.getcwd())


def _launch_app(rpc, bundleid):
    rpc.start()

    def on_channel_message(res):
        if res.raw._auxiliaries:
            for buf in res.raw._auxiliaries:
                print(auxiliary_to_pyobject(buf))

    channel = "com.apple.instruments.server.services.processcontrol"
    rpc.register_channel_callback(channel, on_channel_message)
    pid = rpc.call(channel, "launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments:options:", "",
                   bundleid, {}, [], {"StartSuspendedKey": 0, "KillExisting": 1}).parsed
    print("start", pid)


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    _launch_app(rpc, 'cn.rongcloud.im')
    rpc.stop()

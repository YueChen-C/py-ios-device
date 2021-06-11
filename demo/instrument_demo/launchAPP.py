"""
启动 app
"""
import os
import sys

sys.path.append(os.getcwd())

from ios_device.servers.Instrument import InstrumentServer


def _launch_app(rpc, bundleid):
    rpc._start()

    def on_channel_message(res):
        print(res.auxiliaries, res.selector)

    channel = "com.apple.instruments.server.services.processcontrol"
    rpc.register_channel_callback(channel, on_channel_message)
    pid = rpc.call(channel, "launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments:options:", "",
                   bundleid, {}, [], {"StartSuspendedKey": 0, "KillExisting": 1}).selector
    print("start", pid)


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    _launch_app(rpc, 'cn.rongcloud.im')
    rpc.stop()

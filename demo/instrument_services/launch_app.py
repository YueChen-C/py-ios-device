import os
import sys
from threading import Event

sys.path.append(os.getcwd())
from instrument import RPC


def launch_app(rpc, bundleid):

    def on_channel_message(res):
        print(res)

    rpc.start()
    channel = "com.apple.instruments.server.services.processcontrol"
    rpc.register_channel_callback(channel, on_channel_message)
    pid = rpc.call(channel, "launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments:options:", "",
                   bundleid, {}, [], {"StartSuspendedKey": 0, "KillExisting": 1}).parsed
    print("start", pid)


if __name__ == '__main__':
    rpc = RPC.get_usb_rpc()
    launch_app(rpc, 'cn.rongcloud.im')
    rpc.stop()


"""
监听事件，比如 app 唤醒，杀死，退出到后台等等
"""

from time import sleep

from ios_device.servers.dvt import DTXServer
from ios_device.servers.Instrument import InstrumentServer


def MobileNotifications(rpc: DTXServer):
    def dropped_message(res):
        print("[DROP]", res.selector, res.auxiliaries)
    rpc.register_undefined_callback(dropped_message)

    rpc.call(
        "com.apple.instruments.server.services.mobilenotifications",
        'setApplicationStateNotificationsEnabled:', str(True))
    sleep(5)
    rpc.call(
        "com.apple.instruments.server.services.mobilenotifications",
        'setApplicationStateNotificationsEnabled:', str(False))
    # print("aaaaa")
    sleep(10)
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    MobileNotifications(rpc)
    rpc.stop()

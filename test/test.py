"""
@Date    : 2021-02-24
@Author  : liyachao
"""
import time

from ios_device import py_ios_device
from ios_device.py_ios_device import PyiOSDevice

xcuitest_bundle_id = "cn.xx.autotest.xctrunner"
app_bundle_id = "com.tencent.xin"


def callback(res):
    print(res)


def test_get_process():
    process = py_ios_device.get_processes()
    print(process)


def test_get_process_obj():
    channel = PyiOSDevice()
    process = channel.get_processes()
    print(process)
    channel.stop()


def test_get_channel():
    channels = py_ios_device.get_channel()
    print(channels)


def test_get_channel_obj():
    channel = PyiOSDevice()
    channels = channel.get_channel()
    print(channels)
    channel.stop()


def test_start_get_gpu():
    channel = py_ios_device.start_get_gpu(callback=callback)
    time.sleep(5)
    py_ios_device.stop_get_gpu(channel)
    channel.stop()


def test_start_get_gpu_obj():
    channel = PyiOSDevice()
    channel.start_get_gpu(callback=callback)
    time.sleep(5)
    channel.stop_get_gpu()
    channel.stop()


def test_get_device():
    device = py_ios_device.get_device()
    app_list = device.get_apps()
    print(app_list)
    for index in app_list:
        print(index.get("CFBundleDisplayName"))
        print(index.get("CFBundleIdentifier"))


def test_get_device_obj():
    channel = PyiOSDevice()
    device = channel.get_device()
    app_list = device.get_apps()
    print(app_list)
    channel.stop()


def test_launch_app():
    py_ios_device.launch_app(app_bundle_id)


def test_launch_app_obj():
    channel = PyiOSDevice()
    channel.launch_app(app_bundle_id)
    channel.stop()


def test_get_applications():
    app_list = py_ios_device.get_applications()
    print(app_list)


def test_get_applications_obj():
    channel = PyiOSDevice()
    app_list = channel.get_applications()
    print(app_list)
    channel.stop()


def test_start_xcuitest():
    channel = py_ios_device.start_xcuitest(bundle_id=xcuitest_bundle_id, callback=callback)
    time.sleep(5)
    py_ios_device.stop_xcuitest(channel)
    channel.stop()


def test_start_xcuitest_obj():
    channel = PyiOSDevice()
    channel.start_xcuitest(bundle_id=xcuitest_bundle_id, callback=callback)
    time.sleep(5)
    channel.stop_xcuitest()
    channel.stop()


def test_start_get_fps():
    channel = py_ios_device.start_get_fps(callback=callback)
    time.sleep(5)
    py_ios_device.stop_get_fps(channel)
    channel.stop()


def test_start_get_fps_obj():
    channel = PyiOSDevice()
    channel.start_get_fps(callback=callback)
    time.sleep(5)
    channel.stop_get_fps()
    channel.stop()


def test_start_get_graphics_fps():
    channel = py_ios_device.start_get_graphics_fps(callback=callback)
    time.sleep(5)
    py_ios_device.stop_get_graphics_fps(channel)
    channel.stop()


def test_start_get_graphics_fps_obj():
    channel = PyiOSDevice()
    channel.start_get_graphics_fps(callback=callback)
    time.sleep(5)
    channel.stop_get_graphics_fps()
    channel.stop()


def test_start_get_mobile_notifications():
    channel = py_ios_device.start_get_mobile_notifications(callback=callback)
    time.sleep(5)
    py_ios_device.stop_get_mobile_notifications(channel)
    channel.stop()


def test_start_get_mobile_notifications_obj():
    channel = PyiOSDevice()
    channel.start_get_mobile_notifications(callback=callback)
    time.sleep(5)
    channel.stop_get_mobile_notifications()
    channel.stop()


def test_get_netstat():
    netstat = py_ios_device.get_netstat(216)
    print(netstat)


def test_get_netstat_obj():
    channel = PyiOSDevice()
    netstat = channel.get_netstat(216)
    print(netstat)
    channel.stop()


if __name__ == "__main__":
    # test_get_process()
    # test_get_process_obj()
    # test_get_channel()
    # test_get_channel_obj()
    # test_start_get_gpu()
    # test_start_get_gpu_obj()
    # test_get_device()
    # test_get_device_obj()
    # test_launch_app()
    # test_launch_app_obj()
    # test_get_applications()
    # test_get_applications_obj()
    # test_start_xcuitest()
    # test_start_xcuitest_obj()
    # test_start_get_fps()
    # test_start_get_fps_obj()
    # test_start_get_graphics_fps()
    # test_start_get_graphics_fps_obj()
    # test_start_get_mobile_notifications()
    # test_start_get_mobile_notifications_obj()
    # test_get_netstat()
    test_get_netstat_obj()

"""
@Date    : 2021-02-24
@Author  : liyachao
"""
import time

import pytest
from queue import Queue
from ios_device import py_ios_device
from ios_device.py_ios_device import PyiOSDevice

app_bundle_id = "com.apple.calculator"


class TestIOSDevice:

    def callback(self, res):
        self.queue.put(res)

    @pytest.fixture(autouse=True)
    def create_device(self):
        self.device = PyiOSDevice()
        self.channel = None
        self.queue = Queue()
        yield
        self.device.stop()
        if self.channel is not None:
            self.channel.stop()

    def test_get_process(self):
        process = py_ios_device.get_processes()
        assert len(process) > 0

    def test_get_process_obj(self):
        process = self.device.get_processes()
        assert len(process) > 0

    def test_get_channel(self):
        channels = py_ios_device.get_channel()
        assert channels

    def test_get_channel_obj(self):
        channels = self.device.get_channel()
        assert channels

    def test_start_get_gpu(self):
        self.channel = py_ios_device.start_get_gpu(callback=self.callback)
        msg = self.queue.get(True, timeout=5)
        py_ios_device.stop_get_gpu(self.channel)
        assert msg

    def test_start_get_gpu_obj(self):
        self.device.start_get_gpu(callback=self.callback)
        msg = self.queue.get(True, timeout=5)
        self.device.stop_get_gpu()
        assert msg

    def test_get_device(self):
        device = py_ios_device.get_device()
        app_list = device.get_apps()
        assert len(app_list) > 0
        for index in app_list:
            print(index.get("CFBundleDisplayName"), index.get("CFBundleIdentifier"))
            assert index.get("CFBundleDisplayName")
            assert index.get("CFBundleIdentifier")

    def test_get_device_obj(self):
        app_list = self.device.get_device().get_apps()
        assert len(app_list) > 0
        for index in app_list:
            assert index.get("CFBundleDisplayName")
            assert index.get("CFBundleIdentifier")

    def test_launch_app(self):
        pid = py_ios_device.launch_app(app_bundle_id)
        assert isinstance(pid, int)

    def test_launch_app_obj(self):
        pid = self.device.launch_app(app_bundle_id)
        assert isinstance(pid, int)

    def test_get_applications(self):
        app_list = py_ios_device.get_applications()
        assert len(app_list) > 0

    def test_get_applications_obj(self):
        app_list = self.device.get_applications()
        assert len(app_list) > 0

    def test_start_get_fps(self):
        self.channel = py_ios_device.start_get_fps(callback=self.callback)
        self.device.launch_app(app_bundle_id)
        self.device.launch_app("com.apple.mobilephone")
        msg = self.queue.get(True, timeout=5)
        py_ios_device.stop_get_fps(self.channel)
        assert msg

    def test_start_get_fps_obj(self):
        self.device.start_get_fps(callback=self.callback)
        self.device.launch_app(app_bundle_id)
        self.device.launch_app("com.apple.mobilephone")
        msg = self.queue.get(True, timeout=5)
        self.device.stop_get_fps()
        assert msg

    def test_start_get_graphics_fps(self):
        self.channel = py_ios_device.start_get_graphics_fps(callback=self.callback)
        msg = self.queue.get(True, timeout=5)
        py_ios_device.stop_get_graphics_fps(self.channel)
        assert msg

    def test_start_get_graphics_fps_obj(self):
        self.device.start_get_graphics_fps(callback=self.callback)
        msg = self.queue.get(True, timeout=5)
        self.device.stop_get_graphics_fps()
        assert msg

    def test_start_get_mobile_notifications(self):
        self.channel = py_ios_device.start_get_mobile_notifications(callback=self.callback)
        msg = self.queue.get(True, timeout=5)
        py_ios_device.stop_get_mobile_notifications(self.channel)
        assert msg

    def test_start_get_mobile_notifications_obj(self):
        self.device.start_get_mobile_notifications(callback=self.callback)
        msg = self.queue.get(True, timeout=5)
        self.device.stop_get_mobile_notifications()
        assert msg

    def test_get_netstat(self):
        netstat = py_ios_device.get_netstat(216)
        assert netstat

    def test_get_netstat_obj(self):
        netstat = self.device.get_netstat(216)
        assert netstat

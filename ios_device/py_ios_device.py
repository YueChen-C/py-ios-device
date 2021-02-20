"""
@Date    : 2021-01-28
@Author  : liyachao
"""
import json
import os
import threading
import time
from distutils.version import LooseVersion

from ios_device.servers.house_arrest import HouseArrestClient

from ios_device.util.bpylist import archive

from ios_device.util.dtxlib import get_auxiliary_text

from ios_device.servers.DTXSever import DTXServerRPCRawObj

from ios_device.servers.testmanagerd import TestManagerdLockdown

from ios_device.util._types import NSUUID, XCTestConfiguration, NSURL

from ios_device.servers.InstallationProxy import InstallationProxy

from ios_device.util.lockdown import LockdownClient

from ios_device.servers.Instrument import InstrumentServer
from ios_device.servers.image_mounter import installation_proxy
from ios_device.util import api_util
from ios_device.util.api_util import channel_validate, PyIOSDeviceException, RunXCUITest


class PyiOSDevice:
    def __init__(self, device_id: str = None, rpc_channel: InstrumentServer = None):
        self.device_id = device_id
        self.rpc_channel = None
        if not rpc_channel or not rpc_channel._cli:
            self.init()
        else:
            self.rpc_channel = rpc_channel

    def init(self):
        if not self.rpc_channel:
            self.rpc_channel = init(self.device_id)

    def get_processes(self):
        return get_processes(self.device_id, self.rpc_channel)

    def stop_channel(self):
        self.rpc_channel.deinit()
        self.rpc_channel = None

    def get_channel(self):
        """
        获取当前设备有哪些服务
        :return:
        """

        return self.rpc_channel._published_capabilities

    def start_get_gpu(self, callback):
        """
        开始获取 gpu 数据
        :param callback:
        :return:
        """
        start_get_gpu(device_id=self.device_id, rpc_channel=self.rpc_channel, callback=callback)

    def stop_get_gpu(self):
        """
        结束获取 gpu 数据
        :return:
        """
        stop_get_gpu(self.rpc_channel)

    def launch_app(self, bundle_id: str = None):
        """
        启动 app
        :param bundle_id:
        :return:
        """
        return launch_app(device_id=self.device_id, rpc_channel=self.rpc_channel, bundle_id=bundle_id)

    def start_get_network(self, callback):
        """
        开始获取上下行流量
        :param callback:
        :return:
        """
        start_get_network(device_id=self.device_id, rpc_channel=self.rpc_channel, callback=callback)

    def stop_get_network(self):
        """
        结束获取网络包内容
        :return:
        """
        stop_get_network(rpc_channel=self.rpc_channel)

    def start_get_system(self, callback):
        """
        开始获取系统数据
        :param callback:
        :return:
        """
        start_get_system(device_id=self.device_id, rpc_channel=self.rpc_channel, callback=callback)

    def stop_get_system(self):
        """
        结束获取系统数据
        :return:
        """
        stop_get_system(rpc_channel=self.rpc_channel)

    def get_device(self):
        """
        操作设备
        :return:
        """
        return get_device(device_id=self.device_id, rpc_channel=self.rpc_channel)


def init(device_id: str = None):
    rpc_channel = InstrumentServer(udid=device_id)
    rpc_channel.init()
    return rpc_channel


def get_processes(device_id: str = None, rpc_channel: InstrumentServer = None):
    """
    获取设备的进程列表
    :param rpc_channel:
    :param device_id:
    :return:
    """
    if not rpc_channel:
        rpc_channel = init(device_id)
    validate_result, validate_message = channel_validate(rpc_channel)
    if not validate_result:
        return validate_message
    running = rpc_channel.call("com.apple.instruments.server.services.deviceinfo", "runningProcesses").parsed
    return running


def get_channel(device_id: str = None, rpc_channel: InstrumentServer = None):
    """
    当前设备可用服务列表
    :return:
    """
    if not rpc_channel:
        _rpc_channel = init(device_id)
    else:
        _rpc_channel = rpc_channel
    device_channel = _rpc_channel._published_capabilities
    if not rpc_channel:
        _rpc_channel.stop()
    return device_channel


def start_get_gpu(device_id: str = None, rpc_channel: InstrumentServer = None, callback: object = None,
                  ms_return: bool = False):
    """

    :param device_id:
    :param rpc_channel:
    :param callback:
    :param ms_return:
    :return:
    """

    if not callback:
        raise PyIOSDeviceException("callback can not be None")

    if not rpc_channel:
        _rpc_channel = init(device_id)
    else:
        _rpc_channel = rpc_channel

    def _callback(res):
        api_util.caller(res, callback)

    if ms_return:
        _rpc_channel.call("com.apple.instruments.server.services.graphics.opengl", "setSamplingRate:", 0.0)
    _rpc_channel.call("com.apple.instruments.server.services.graphics.opengl",
                      "startSamplingAtTimeInterval:processIdentifier:",
                      0.0, 0.0)
    _rpc_channel.register_channel_callback("com.apple.instruments.server.services.graphics.opengl", _callback)

    return _rpc_channel


def stop_get_gpu(rpc_channel: InstrumentServer):
    """
    停止获取 gpu 性能数据
    :param rpc_channel:
    :return:
    """
    rpc_channel.call("com.apple.instruments.server.services.graphics.opengl", "stopSampling")


def launch_app(bundle_id: str, device_id: str = None, rpc_channel: InstrumentServer = None):
    """
    启动 app
    :param device_id:
    :param rpc_channel:
    :param bundle_id:
    :return:
    """

    if not rpc_channel:
        _rpc_channel = init(device_id)
    else:
        _rpc_channel = rpc_channel

    channel_name = "com.apple.instruments.server.services.processcontrol"
    _rpc_channel.register_channel_callback(channel_name, lambda x: x)
    pid = _rpc_channel.call(channel_name,
                            "launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments:options:", "",
                            bundle_id, {}, [], {"StartSuspendedKey": 0, "KillExisting": 1}).parsed
    if not rpc_channel:
        _rpc_channel.stop()
    return pid


def start_get_network(callback: object, device_id: str = None, rpc_channel: InstrumentServer = None, ):
    """
    开始获取网络包内容
    :param device_id:
    :param rpc_channel:
    :param callback:
    :return:
    """

    if not rpc_channel:
        _rpc_channel = init(device_id)
    else:
        _rpc_channel = rpc_channel

    def _callback(res):
        api_util.network_caller(res, callback)

    _rpc_channel.register_channel_callback("com.apple.instruments.server.services.networking", _callback)
    _rpc_channel.call("com.apple.instruments.server.services.networking", "replayLastRecordedSession")
    _rpc_channel.call("com.apple.instruments.server.services.networking", "startMonitoring")
    return _rpc_channel


def stop_get_network(rpc_channel: InstrumentServer):
    """
    结束获取网络包内容
    :param rpc_channel:
    :return:
    """
    rpc_channel.call("com.apple.instruments.server.services.networking", "stopMonitoring")


# def start_get_power_data(device_id: str = None, rpc_channel: InstrumentServer = None, callback: object = None):
#     """
#     开始获取电量数据
#     :param device_id:
#     :param rpc_channel:
#     :param callback:
#     :return:
#     """
#     if not callback:
#         raise PyIOSDeviceException("callback can not be None")
#
#     if not rpc_channel:
#         _rpc_channel = init(device_id)
#     else:
#         _rpc_channel = rpc_channel
#
#     def _callback(res):
#         api_util.power_caller(res, callback)
#
#     channel_name = "com.apple.instruments.server.services.power"
#     _rpc_channel.register_channel_callback(channel_name, _callback)
#     stream_num = _rpc_channel.call(channel_name, "openStreamForPath:", "live/level.dat").parsed
#     _rpc_channel.call(channel_name, "startStreamTransfer:", float(stream_num))
#     return _rpc_channel,stream_num

# def stop_get_power_data(rpc_channel: InstrumentServer = None, stream_num: float = None):
#     """
#     结束获取电量数据
#     :param stream_num:
#     :param rpc_channel:
#     :return:
#     """
#     if not stream_num:
#         raise PyIOSDeviceException("stream_num can not be None")
#     if not rpc_channel:
#         raise PyIOSDeviceException("rpc_channel can not be None")
#     rpc_channel.call(channel, "endStreamTransfer:", float(stream_num))


def start_get_system(device_id: str = None, rpc_channel: InstrumentServer = None, callback: object = None):
    """
    开始获取系统数据
    :param device_id:
    :param rpc_channel:
    :param callback:
    :return:
    """
    if not callback:
        raise PyIOSDeviceException("callback can not be None")

    if not rpc_channel:
        _rpc_channel = init(device_id)
    else:
        _rpc_channel = rpc_channel

    def _callback(res):
        api_util.system_caller(res, callback)

    _rpc_channel.register_unhandled_callback(lambda x: x)
    _rpc_channel.call("com.apple.instruments.server.services.sysmontap", "setConfig:", {
        'ur': 1000,  # 输出频率 ms
        'bm': 0,
        'procAttrs': ['memVirtualSize', 'cpuUsage', 'procStatus', 'appSleep', 'uid', 'vmPageIns', 'memRShrd',
                      'ctxSwitch', 'memCompressed', 'intWakeups', 'cpuTotalSystem', 'responsiblePID', 'physFootprint',
                      'cpuTotalUser', 'sysCallsUnix', 'memResidentSize', 'sysCallsMach', 'memPurgeable',
                      'diskBytesRead', 'machPortCount', '__suddenTerm', '__arch', 'memRPrvt', 'msgSent', 'ppid',
                      'threadCount', 'memAnon', 'diskBytesWritten', 'pgid', 'faults', 'msgRecv', '__restricted', 'pid',
                      '__sandbox'],  # 输出所有进程信息字段，字段顺序与自定义相同（全量自字段，按需使用）
        'sysAttrs': ['diskWriteOps', 'diskBytesRead', 'diskBytesWritten', 'threadCount', 'vmCompressorPageCount',
                     'vmExtPageCount', 'vmFreeCount', 'vmIntPageCount', 'vmPurgeableCount', 'netPacketsIn',
                     'vmWireCount', 'netBytesIn', 'netPacketsOut', 'diskReadOps', 'vmUsedCount', '__vmSwapUsage',
                     'netBytesOut'],  # 系统信息字段
        'cpuUsage': True,
        'sampleInterval': 1000000000})
    _rpc_channel.register_channel_callback("com.apple.instruments.server.services.sysmontap", _callback)
    _rpc_channel.call("com.apple.instruments.server.services.sysmontap", "start")
    return _rpc_channel


def stop_get_system(rpc_channel: InstrumentServer = None):
    """
    结束获取系统数据
    :param rpc_channel:
    :return:
    """
    if not rpc_channel:
        raise PyIOSDeviceException("rpc_channel can not be None")
    rpc_channel.call("com.apple.instruments.server.services.sysmontap", "stop")


def get_device(device_id: str = None, rpc_channel: InstrumentServer = None):
    """
    操作设备
    :param device_id:
    :param rpc_channel:
    :return:
    """
    current_device = installation_proxy(udid=device_id, lockdown=rpc_channel)
    return current_device


def get_applications(device_id: str = None, rpc_channel: InstrumentServer = None):
    """
    获取手机应用列表
    :param device_id:
    :param rpc_channel:
    :return:
    """
    if not rpc_channel:
        _rpc_channel = init(device_id)
    else:
        _rpc_channel = rpc_channel
    application_list = _rpc_channel.call(
        "com.apple.instruments.server.services.device.applictionListing",
        "installedApplicationsMatching:registerUpdateToken:",
        {}, "").parsed
    if not rpc_channel:
        _rpc_channel.stop()
    return application_list


def start_xcuitest(bundle_id: str, callback, device_id: str = None, app_env: dict = None):
    xcuitest = RunXCUITest(bundle_id=bundle_id, callback=callback, device_id=device_id, app_env=app_env)
    xcuitest.start()
    return xcuitest


def stop_xcuitest(xcuitest):
    xcuitest.close()


def te1st(res):
    print(res[0]["PerCPUUsage"])
    print(res)


if __name__ == "__main__":
    # x = start_xcuitest("cn.rongcloud.rce.autotest.xctrunner", te1st,app_env={'USE_PORT': '8111'})
    # time.sleep(10)
    # stop_xcuitest(x)

    system = start_get_system(callback=te1st)
    time.sleep(10)
    stop_get_system(system)
    # processes = channel.start_get_gpu_data(callba)
    # print(processes)
    # channel.stop_channel()

    # 有开始 有结束的demo
    # channel = init()
    # start_get_network(rpc_channel=channel, callback=te1st)
    # time.sleep(10)
    # stop_get_network(rpc_channel=channel)
    # channel.stop()

    # 普通的demo
    # channel = get_channel()
    # print(channel)
    # get_device()

    # channel = PyiOSDevice()
    # print(channel.get_channel())

    # channel = start_get_power_data(callback=test)
    # # time.sleep(10)
    # # stop_get_system_data(channel)
    # channel.stop()

    # device = get_device()
    # print(device.get_apps_bid())
    import dataclasses

    pass

    # channel.register_unhandled_callback(test)
    # channel.register_callback("_notifyOfPublishedCapabilities:", lambda a: print(1))
    # start_get_gpu_data(rpc_channel=channel, callback=test)
    # time.sleep(2)
    # stop_get_gpurpc_channel=channel,_data(channel)
    # channel.get_processes()
    # process = channel.get_processes()
    # print(process)
    # channel.start_activity(242)
    # print(get_channel(rpc_channel=channel))
    # dc = channel.get_processes()
    # print(dc)
    # channel.stop_channel()

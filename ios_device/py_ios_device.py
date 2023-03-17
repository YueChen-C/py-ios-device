"""
@Date    : 2021-01-28
@Author  : liyachao
"""
import uuid
from datetime import datetime


from ios_device.util.exceptions import InstrumentRPCParseError
from ios_device.servers.Installation import InstallationProxyService
from ios_device.servers.Instrument import InstrumentServer
from ios_device.util import api_util
from ios_device.util.api_util import PyIOSDeviceException, RunXCUITest
from ios_device.util.forward import ForwardPorts
from ios_device.util.kperf_data import KperfData
from ios_device.util.utils import kperf_data


class PyiOSDevice:
    def __init__(self, device_id: str = None, rpc_channel: InstrumentServer = None):
        self.device_id = device_id
        self.xcuitest = None
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

    def stop(self):
        self.rpc_channel.stop()

    def get_channel(self):
        """
        获取当前设备有哪些服务
        :return:
        """

        return self.rpc_channel._published_capabilities

    def start_get_gpu(self, callback: callable):
        """
        开始获取 gpu 数据
        :param callback:
        :return:
        """
        return start_get_gpu(device_id=self.device_id, rpc_channel=self.rpc_channel, callback=callback)

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

    def start_get_network(self, callback: callable):
        """
        开始获取上下行流量
        :param callback:
        :return:
        """
        return start_get_network(device_id=self.device_id, rpc_channel=self.rpc_channel, callback=callback)

    def stop_get_network(self):
        """
        结束获取网络包内容
        :return:
        """
        stop_get_network(rpc_channel=self.rpc_channel)

    def start_get_system(self, callback: callable):
        """
        开始获取系统数据
        :param callback:
        :return:
        """
        return start_get_system(device_id=self.device_id, rpc_channel=self.rpc_channel, callback=callback)

    def stop_get_system(self):
        """
        结束获取系统数据
        :return:
        """
        stop_get_system(rpc_channel=self.rpc_channel)

    def get_device(self):
        """
        获取设备对象用于操作设备
        :return:
        """
        return get_device(device_id=self.device_id, rpc_channel=self.rpc_channel)

    def get_applications(self):
        """
        获取手机应用列表
        :return:
        """
        return get_applications(device_id=self.device_id, rpc_channel=self.rpc_channel)

    def start_xcuitest(self, bundle_id, callback: callable, app_env: dict = None,
                       pair_ports=None):
        """
        启动 xcuittest
        :param pair_ports: 端口对的数组，每对端口中前一个代表远程端口，后一个代表本地端口，例如：["8100:8100", "8200:8200"]
        :param forward: 是否进行端口转发
        :param bundle_id:
        :param callback:
        :param app_env:
        :return:
        """

        self.xcuitest = start_xcuitest(bundle_id, callback, self.device_id, app_env, pair_ports)
        return self.xcuitest

    def stop_xcuitest(self, xcuitest=None):
        """
        停止 xcuitest
        :param xcuitest:
        :return:
        """
        if not xcuitest and not self.xcuitest:
            raise PyIOSDeviceException("xcuitest object can not be None")
        stop_xcuitest(xcuitest if xcuitest else self.xcuitest)

    def start_get_fps(self, callback: callable):
        """
        开始获取 fps 相关数据
        :param callback:
        :return:
        """
        return start_get_fps(device_id=self.device_id, rpc_channel=self.rpc_channel, callback=callback)

    def stop_get_fps(self):
        """
        结束获取 fps 相关数据
        :return:
        """
        stop_get_fps(rpc_channel=self.rpc_channel)

    def get_energy(self, pid: int):
        get_energy(pid=pid, device_id=self.device_id, rpc_channel=self.rpc_channel)

    def start_get_graphics_fps(self, callback: callable):
        """
        graphics 计算 fps
        :param callback:
        :return:
        """
        start_get_graphics_fps(device_id=self.device_id, rpc_channel=self.rpc_channel, callback=callback)

    def stop_get_graphics_fps(self):
        stop_get_graphics_fps(rpc_channel=self.rpc_channel)

    def start_get_mobile_notifications(self, callback: callable):
        """
        监听事件，比如 app 唤醒，杀死，退出到后台等等
        :param callback:
        :return:
        """
        start_get_mobile_notifications(device_id=self.device_id, rpc_channel=self.rpc_channel, callback=callback)

    def stop_get_mobile_notifications(self):
        stop_get_mobile_notifications(rpc_channel=self.rpc_channel)

    def get_netstat(self, pid: int):
        """
        获取单应用的网络信息
        :param pid:
        :return:
        """
        return get_netstat(pid=pid, device_id=self.device_id, rpc_channel=self.rpc_channel)

    def start_forward(self, pair_ports=None):
        """
        iOS真机设备的端口转发
        :param pair_ports: list 端口对的数组，每对端口中前一个代表远程端口，后一个代表本地端口，例如：["8100:8100", "8200:8200"]
        :param udid:
        :param threaded:
        :param bufsize:
        """
        return start_forward(pair_ports=pair_ports, device_id=self.device_id)

    def stop_forward(self, forward: ForwardPorts):
        stop_forward(forward)


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
        _rpc_channel = init(device_id)
    else:
        _rpc_channel = rpc_channel
    running = _rpc_channel.call("com.apple.instruments.server.services.deviceinfo", "runningProcesses").selector
    if not rpc_channel:
        _rpc_channel.stop()
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


def start_get_gpu(device_id: str = None, rpc_channel: InstrumentServer = None, callback: callable = None,
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
                            bundle_id, {}, [], {"StartSuspendedKey": 0, "KillExisting": 1}).selector
    if not rpc_channel:
        _rpc_channel.stop()
    return pid


def start_get_network(callback: callable, device_id: str = None, rpc_channel: InstrumentServer = None, ):
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


def start_get_system(device_id: str = None, rpc_channel: InstrumentServer = None, callback: callable = None):
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

    _rpc_channel.register_undefined_callback(lambda x: x)
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


def stop_get_system(rpc_channel: InstrumentServer):
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
    获取设备对象用于操作设备
    :param device_id:
    :param rpc_channel:
    :return:
    """
    current_device = InstallationProxyService(udid=device_id, lockdown=rpc_channel.lockdown if rpc_channel else None)
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
        {}, "").selector
    if not rpc_channel:
        _rpc_channel.stop()
    return application_list


def start_xcuitest(bundle_id: str, callback: callable, device_id: str = None, app_env: dict = None,
                   pair_ports=None):
    """
    启动 xcuittest
    :param pair_ports: 端口对的数组，每对端口中前一个代表远程端口，后一个代表本地端口，例如：["8100:8100", "8200:8200"]
    :param bundle_id:
    :param callback:
    :param device_id:
    :param app_env: 启动配置 {
            'CA_ASSERT_MAIN_THREAD_TRANSACTIONS': '0',
            'CA_DEBUG_TRANSACTIONS': '0',
            'DYLD_FRAMEWORK_PATH': app_path + '/Frameworks:',
            'DYLD_LIBRARY_PATH': app_path + '/Frameworks',
            'NSUnbufferedIO': 'YES',
            'SQLITE_ENABLE_THREAD_ASSERTIONS': '1',
            'WDA_PRODUCT_BUNDLE_IDENTIFIER': '',
            'XCTestConfigurationFilePath': xctestconfiguration_path,
            'XCODE_DBG_XPC_EXCLUSIONS': 'com.apple.dt.xctestSymbolicator',
            'MJPEG_SERVER_PORT': '',
            'USE_PORT': '',
        }
    :return: 返回 xcuitest 对象,用于停止 xcuitest
    """

    if pair_ports is None:
        pair_ports = ["8100:8100"]
    xcuitest = RunXCUITest(bundle_id=bundle_id, callback=callback, device_id=device_id, app_env=app_env,
                           pair_ports=pair_ports)

    xcuitest.start()
    return xcuitest


def stop_xcuitest(xcuitest):
    """
    停止 xcuitest
    :param xcuitest: 启动时可获取对象
    :return:
    """
    if type(xcuitest) == RunXCUITest:
        xcuitest.stop()
    else:
        raise PyIOSDeviceException("参数类型必须是 RunXCUITest")


def start_get_fps(device_id: str = None, rpc_channel: InstrumentServer = None, callback: callable = None):
    from statistics import mean
    """
    开始获取 fps 相关数据
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

    NANO_SECOND = 1e9  # ns
    MOVIE_FRAME_COST = 1 / 24
    last_frame = None
    last_1_frame_cost, last_2_frame_cost, last_3_frame_cost = 0, 0, 0
    jank_count = 0
    big_jank_count = 0
    jank_time_count = 0
    mach_time_factor = 125 / 3
    frame_count = 0
    time_count = 0
    count_time = datetime.now().timestamp()
    _list = []

    def _callback(res):
        nonlocal frame_count, last_frame, last_1_frame_cost, last_2_frame_cost, last_3_frame_cost, time_count, mach_time_factor, \
            jank_count, big_jank_count, jank_time_count, _list, count_time
        if type(res.selector) is InstrumentRPCParseError:
            for args in kperf_data(res.selector.data):
                _time, code = args[0], args[7]
                if code == 830472984:
                    if not last_frame:
                        last_frame = _time
                    else:
                        this_frame_cost = (_time - last_frame) * mach_time_factor
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
                        last_frame = _time
                        frame_count += 1
                # else:
                #     time_count = (datetime.now().timestamp() - count_time) * NANO_SECOND
                if time_count > NANO_SECOND:
                    callback(
                        {"currentTime": str(datetime.now()), "FPS": frame_count / time_count * NANO_SECOND,
                         "jank": jank_count,
                         "big_jank": big_jank_count, "stutter": jank_time_count / time_count})
                    jank_count = 0
                    big_jank_count = 0
                    jank_time_count = 0
                    frame_count = 0
                    time_count = 0
                    count_time = datetime.now().timestamp()

    Kperf = KperfData()
    _rpc_channel.register_undefined_callback(lambda x: x)
    # 获取mach time比例
    mach_time_info = _rpc_channel.call("com.apple.instruments.server.services.deviceinfo", "machTimeInfo").selector
    mach_time_factor = mach_time_info[1] / mach_time_info[2]
    _rpc_channel.register_channel_callback("com.apple.instruments.server.services.coreprofilesessiontap",
                                           _callback)

    _rpc_channel.call("com.apple.instruments.server.services.coreprofilesessiontap", "setConfig:",
                      {'rp': 10,
                       'tc': [{'kdf2': {630784000, 833617920, 830472456},
                               'tk': 3,
                               'uuid': str(uuid.uuid4()).upper()}],
                       'ur': 500})

    _rpc_channel.call("com.apple.instruments.server.services.coreprofilesessiontap", "start")

    return _rpc_channel


def stop_get_fps(rpc_channel: InstrumentServer):
    """
    结束获取 fps 数据
    :param rpc_channel:
    :return:
    """
    if not rpc_channel:
        raise PyIOSDeviceException("rpc_channel can not be None")
    rpc_channel.call("com.apple.instruments.server.services.coreprofilesessiontap", "stop")


def get_energy(pid: int, device_id: str = None, rpc_channel: InstrumentServer = None):
    if not rpc_channel:
        _rpc_channel = init(device_id)
    else:
        _rpc_channel = rpc_channel

    channel_name = "com.apple.xcode.debug-gauge-data-providers.Energy"
    attr = {}
    # _rpc_channel.call(channel_name, "startSamplingForPIDs:", {pid})
    ret = _rpc_channel.call(channel_name, "sampleAttributes:forPIDs:", attr, {pid})
    if not rpc_channel:
        _rpc_channel.stop()
    return ret.selector


def start_get_graphics_fps(device_id: str = None, rpc_channel: InstrumentServer = None, callback: callable = None):
    """
    graphics 计算 fps
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
        data = res.selector
        callback({"currentTime": str(datetime.now()), "fps": data['CoreAnimationFramesPerSecond']})

    _rpc_channel.register_undefined_callback(lambda x: x)
    _rpc_channel.register_channel_callback("com.apple.instruments.server.services.graphics.opengl", _callback)
    _rpc_channel.call("com.apple.instruments.server.services.graphics.opengl", "startSamplingAtTimeInterval:", 0.0)
    return _rpc_channel


def stop_get_graphics_fps(rpc_channel: InstrumentServer):
    """
    停止获取 graphics 计算 fps
    :param rpc_channel:
    :return:
    """
    if not rpc_channel:
        raise PyIOSDeviceException("rpc_channel can not be None")
    rpc_channel.call("com.apple.instruments.server.services.graphics.opengl", "stopSampling")


def start_get_mobile_notifications(device_id: str = None, rpc_channel: InstrumentServer = None,
                                   callback: callable = None):
    """
    监听事件，比如 app 唤醒，杀死，退出到后台等等
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
        callback(res)

    _rpc_channel.register_channel_callback("com.apple.instruments.server.services.mobilenotifications", _callback)

    _rpc_channel.call(
        "com.apple.instruments.server.services.mobilenotifications",
        'setApplicationStateNotificationsEnabled:', str(True))
    return _rpc_channel


def stop_get_mobile_notifications(rpc_channel: InstrumentServer):
    """

    :param rpc_channel:
    :return:
    """
    rpc_channel.call(
        "com.apple.instruments.server.services.mobilenotifications",
        'setApplicationStateNotificationsEnabled:', str(False))


def get_netstat(pid: int, device_id: str = None, rpc_channel: InstrumentServer = None):
    """
    获取单应用的网络信息
    :param device_id:
    :param rpc_channel:
    :param callback:
    :return:
    """

    if not rpc_channel:
        _rpc_channel = init(device_id)
    else:
        _rpc_channel = rpc_channel
    channel = "com.apple.xcode.debug-gauge-data-providers.NetworkStatistics"
    attr = {}
    # print("start", _rpc_channel.call(channel, "startSamplingForPIDs:", {pid}).selector)
    ret = _rpc_channel.call(channel, "sampleAttributes:forPIDs:", attr, {pid}).selector
    if not rpc_channel:
        _rpc_channel.stop()
    return ret


def start_forward(pair_ports=None, device_id: str = None):
    """
    iOS真机设备的端口转发
        :param pair_ports: list 端口对的数组，每对端口中前一个代表远程端口，后一个代表本地端口，例如：["8100:8100", "8200:8200"]
        :param device_id:
    :return:
    """
    if not pair_ports:
        pair_ports = ["8100,8100"]
    forward = ForwardPorts(pair_ports=pair_ports, device_id=device_id)
    forward.start()
    return forward


def stop_forward(forward: ForwardPorts):
    forward.stop()

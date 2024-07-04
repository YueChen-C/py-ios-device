import os
import plistlib
import threading
import uuid
from packaging.version import Version

from ios_device.servers.Installation import InstallationProxyService
from ios_device.servers.Instrument import InstrumentServer
from ios_device.servers.dvt import DTXEnum
from ios_device.servers.house_arrest import HouseArrestService
from ios_device.servers.testmanagerd import TestManagerdLockdown
from ios_device.util import Log
from ios_device.util.lifecycle import AppLifeCycle
from ios_device.util.bpylist2 import NSUUID, NSURL, XCTestConfiguration
from ios_device.util.bpylist2 import archive
from ios_device.util.dtx_msg import RawObj, RawInt32sl, RawInt64sl
from ios_device.util.exceptions import InstrumentRPCParseError
from ios_device.util.kperf_data import KperfData, KdBufParser
from ios_device.util.lockdown import LockdownClient
from ios_device.util.variables import InstrumentsService, LOG

log = Log.getLogger(LOG.Instrument.value)


class InstrumentDeviceInfo:
    def __exit__(self):
        self.rpc.stop()

    def __init__(self, rpc: InstrumentServer):
        self.rpc = rpc

    def runningProcesses(self):
        """ Get a list of running applications; 获取当前运行应用
        :return:
        """
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "runningProcesses").selector
        return parsed

    def execnameForPid(self, pid: str):
        """ Get the application name running pid; 获取 pid 应用名称
        :param pid:
        :return:
        """
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "execnameForPid:", str(pid)).selector
        return parsed

    def isRunningPid(self, pid: str):
        """ Is the app running ; 应用是否运行
        :param pid:
        :return:
        """
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "isRunningPid:", str(pid)).selector
        return parsed

    def nameForUID(self, uid: str):
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "nameForUID:", str(uid)).selector
        return parsed

    def machTimeInfo(self):
        """ 时间校准，获取
        :return: [mach_absolute_time, numer, denom]
        """
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "machTimeInfo").selector
        return parsed

    def traceCodesFile(self):
        """ code for stack data
        :return: {code: name}
        """
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "traceCodesFile").selector
        return {int(k, 16): v for k, v in map(lambda l: l.split(), parsed.splitlines())}

    def networkInformation(self):
        """ 当前网络信息
        :return: {'en0': 'Wi-Fi', 'en1': 'Ethernet Adaptor (en1)', 'lo0': 'Loopback'}
        """
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "networkInformation").selector
        return parsed

    def systemInformation(self):
        """ system information
        :return:
        """
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "systemInformation").selector
        return parsed

    def hardwareInformation(self):
        """ hardware Information
        :return:
        """
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "hardwareInformation").selector
        return parsed

    def sysmonProcessAttributes(self):
        """ Parameters required to obtain application performance data, 获取应用性能数据所需的参数
        for the 'com.apple.instruments.server.services.sysmontap' service.
        :return:
        """
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "sysmonProcessAttributes").selector
        return parsed

    def sysmonSystemAttributes(self):
        """ Parameters needed to obtain system performance data; 获取系统性能数据所需的参数
        for the 'com.apple.instruments.server.services.sysmontap' service.
        :return:
        """
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "sysmonSystemAttributes").selector
        return parsed

    def symbolicatorSignaturesForExpiredPids(self):
        parsed = self.rpc.call(InstrumentsService.DeviceInfo,
                               "symbolicatorSignaturesForExpiredPids").selector
        return parsed

    def directoryListingForPath(self, path: str):
        """ 监听文件夹路径
        :param path:
        :return:
        """
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "directoryListingForPath:",
                               path).selector
        return parsed

    def iconDescriptionFileForAppPath(self, path: str):
        """ 获取应用 icon 数据
        :param path: /private/var/containers/Bundle/Application/A86066DC-C145-4900-90E7-6FB0CF72215A/smoba.app
        :return:
        """

        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "iconDescriptionFileForAppPath:",
                               path).selector
        return parsed

    def kpepDatabase(self):
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "kpepDatabase").selector
        return plistlib.loads(parsed)

    def machKernelName(self):
        parsed = self.rpc.call(InstrumentsService.DeviceInfo, "machKernelName").selector
        return parsed


class InstrumentsBase:
    def __init__(self, udid=None, network=None, lockdown=None):
        self.udid = udid
        self.network = network
        self.instruments_rcp = None
        self.manager_rpc = None
        self.lockdown = lockdown or LockdownClient(udid=udid, network=network)
        self.process_attributes = None
        self.system_attributes = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.instruments_rcp:
            self.instruments_rcp.stop()
        if self.manager_rpc:
            self.manager_rpc.stop()

    def get_pid(self, bundle_id=None, name=None):
        pid = None
        if bundle_id:
            app = self.application_listing(bundle_id)
            if app:
                name = app.get('ExecutableName')

        if name:
            processes = self.device_info.runningProcesses()
            for p in processes:
                if name == p.get('name'):
                    pid = p.get('pid')
        return pid

    @property
    def instruments(self):
        if self.instruments_rcp:
            return self.instruments_rcp
        self.instruments_rcp = InstrumentServer(lockdown=self.lockdown).init()
        return self.instruments_rcp

    @property
    def manager_lockdown(self):
        if self.manager_rpc:
            return self.manager_rpc
        self.manager_rpc = TestManagerdLockdown(lockdown=self.lockdown).init()
        return self.manager_rpc

    @property
    def device_info(self) -> InstrumentDeviceInfo:
        rpc = self.instruments
        return InstrumentDeviceInfo(rpc)

    def launch_app(self, bundle_id,
                   app_env: dict = None,
                   app_args: list = None,
                   app_path: str = "",
                   options: {} = None,
                   callback: callable = None):
        """
        launch app ; 启动应用
        @param bundle_id: bundle id
        @param app_env:  App running environment variables; 应用运行环境变量
        @param app_args: Parameters required when the app starts; 应用启动时所需参数
        @param app_path: The absolute path of the app usually does not need this parameter,which is used to prevent the
        same bundle id
        @param options:  startup options; 启动选项
        @param callback: callback function will return the app log; 回调函数会持续返回 app 日志
        @return:
        """
        options = options or {
            "StartSuspendedKey": 0,
            "KillExisting": False,
        }
        if callback:
            self.instruments.register_channel_callback(InstrumentsService.ProcessControl, callback)
        pid = self.instruments.call(InstrumentsService.ProcessControl,
                                    "launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments"
                                    ":options:",
                                    app_path, bundle_id, app_env or {}, app_args or [], options or {}).selector
        log.info(f'launch {bundle_id} pid: {pid}')
        return pid

    def kill_app(self, pid: str):
        """
        kill app; 杀死应用
        @param pid:
        @return:
        """
        parsed = self.instruments.call(InstrumentsService.ProcessControl, "killPid:", str(pid)).selector
        return parsed

    def signal_app(self, sig: str, pid: str):
        """
        send signal to app; 向应用发送信号
        @param sig:
        @param pid:
        @return:
        """
        parsed = self.instruments.call(InstrumentsService.ProcessControl, "sendSignal:toPid", str(sig),
                                       str(pid)).selector
        return parsed

    def application_listing(self, bundle_id=None):
        """
        Get the list of installed applications; 获取已安装应用列表
        @param bundle_id:  bundle id
        @return:
        """
        applist = self.instruments.call(InstrumentsService.ApplicationListing,
                                        "installedApplicationsMatching:registerUpdateToken:",
                                        {}, "").selector
        if bundle_id is not None:
            for app in applist:
                if app.get('CFBundleIdentifier') == bundle_id:
                    return app
            else:
                return None
        return applist

    def sysmontap(self,
                  callback: callable,
                  time: int = 1000,
                  stopSignal: threading.Event = threading.Event(),
                  system_attributes=None,
                  process_attributes=None):
        """
        Get application performance data ; 获取性能数据
        @param process_attributes:
        @param system_attributes:
        @param callback:
        @param time: Output frequency (ms)
        @param stopSignal:
        @return:
        """
        config = {
            'ur': time,
            'bm': 0,
            'cpuUsage': True,
            'sampleInterval': time * 1000000}
        _system_attributes = self.system_attributes or system_attributes
        if _system_attributes:
            config['sysAttrs'] = list(_system_attributes)
        _process_attributes = self.process_attributes or process_attributes
        if _process_attributes:
            config['procAttrs'] = list(_process_attributes)
        self.instruments.call(InstrumentsService.Sysmontap, "setConfig:", config)
        self.instruments.register_channel_callback(InstrumentsService.Sysmontap, callback)
        self.instruments.call(InstrumentsService.Sysmontap, "start")
        log.info(f'Sysmontap start ...')
        log.info(f'wait for data ...')
        while not stopSignal.wait(1):
            pass
        self.instruments.call(InstrumentsService.Sysmontap, "stop")

    def graphics(self,
                 callback: callable,
                 time=1000,
                 stopSignal: threading.Event = threading.Event()):
        """
        get graphics
        :param time: Output frequency (ms)
        :param callback:
        :param stopSignal:
        :return:
        """
        self.instruments.register_channel_callback(InstrumentsService.GraphicsOpengl, callback)
        log.info(self.instruments.call(InstrumentsService.GraphicsOpengl, "availableStatistics").selector)
        log.info(self.instruments.call(InstrumentsService.GraphicsOpengl, "driverNames").selector)
        self.instruments.call(InstrumentsService.GraphicsOpengl, "setSamplingRate:",
                              float(time / 100))
        self.instruments.call(InstrumentsService.GraphicsOpengl,
                              "startSamplingAtTimeInterval:",
                              0.0)
        while not stopSignal.wait(1):
            pass
        self.instruments.call(InstrumentsService.GraphicsOpengl, "stopSampling")

    def xcode_network(self, pid, stopSignal: threading.Event = threading.Event()):
        """
        Get the network data of the launched application
        @param pid:
        @param stopSignal:
        @return:
        """
        channel = "com.apple.xcode.debug-gauge-data-providers.NetworkStatistics"
        attr = {}
        self.instruments.call(channel, "startSamplingForPIDs:", {pid})
        while not stopSignal.wait(1):
            ret = self.instruments.call(channel, "sampleAttributes:forPIDs:", attr, {pid})
            print(ret.selector)

    def networking(self,
                   callback: callable,
                   stopSignal: threading.Event = threading.Event()):
        """
        Get system network data
        @param callback:
        @param stopSignal:
        @return:
        """
        self.instruments.register_channel_callback(InstrumentsService.Networking, callback)

        self.instruments.call(InstrumentsService.Networking, "replayLastRecordedSession")
        log.info(msg=f'networking replayLastRecordedSession')
        self.instruments.call(InstrumentsService.Networking, "startMonitoring")
        log.info(msg=f'networking startMonitoring networking')
        self.instruments.register_selector_callback(DTXEnum.FINISHED, lambda _: stopSignal.set())
        while not stopSignal.wait(1):
            pass
        self.instruments.call(InstrumentsService.Networking, "stopMonitoring")
        log.info(msg=f'networking stopMonitoring ')

    def mobile_notifications(self,
                             callback: callable,
                             stopSignal: threading.Event = threading.Event()):
        """
        get mobile notifications
        @param callback:
        @param stopSignal:
        @return:
        """

        self.instruments.register_undefined_callback(callback)
        self.instruments.call(InstrumentsService.MobileNotifications,
                              'setApplicationStateNotificationsEnabled:', str(True))
        log.info(msg='Waiting for action app')
        while not stopSignal.wait(1):
            pass
        self.instruments.call(InstrumentsService.MobileNotifications,
                              'setApplicationStateNotificationsEnabled:', str(False))

    def core_profile_session(self,
                             callback: callable,
                             stopSignal: threading.Event = threading.Event(),
                             config=None):
        if config is None:
            config = {'rp': 10,
                      'tc': [{'kdf2': {630784000, 833617920, 830472456},
                              'tk': 3,
                              'uuid': str(uuid.uuid4()).upper()}],
                      'ur': 500}
        self.instruments.register_channel_callback(InstrumentsService.CoreProfileSessionTap,
                                                   callback)
        self.instruments.call(InstrumentsService.CoreProfileSessionTap, "setConfig:", config)
        self.instruments.call(InstrumentsService.CoreProfileSessionTap, "start")
        while not stopSignal.wait(1):
            pass
        self.instruments.call(InstrumentsService.CoreProfileSessionTap, "stop")

    def gpu_counters(self,
                     callback: callable,
                     stopSignal: threading.Event = threading.Event()):
        """
        get gpu counters
        @param callback:
        @param stopSignal:
        @return:
        """
        self.instruments.register_undefined_callback(callback)
        requestDeviceGPUInfo = self.instruments.call(InstrumentsService.GPU, 'requestDeviceGPUInfo').selector

        min_collection_interval = requestDeviceGPUInfo[0].get('min-collection-interval')
        self.instruments.call(InstrumentsService.GPU,
                              "configureCounters:counterProfile:interval:windowLimit:tracingPID:",
                              RawInt64sl(min_collection_interval, 3, 1, 0), RawInt32sl(-1))
        self.instruments.call(InstrumentsService.GPU, 'startCollectingCounters')
        log.info('Wait for gpu counters data ...')
        while not stopSignal.wait(1):
            pass
        self.instruments.call(InstrumentsService.GPU, 'stopCollectingCounters')
        data = self.instruments.call(InstrumentsService.GPU, 'flushRemainingData').selector
        return data

    def screenshot(self):
        """
        screenshot
        @return:
        """
        var = self.instruments.call(InstrumentsService.Screenshot, "takeScreenshot").selector
        return var

    def power(self,
              callback: callable,
              stopSignal: threading.Event = threading.Event()):
        """
        get power  ios < 14
        @param callback:
        @param stopSignal:
        @return:
        """
        channel = "com.apple.instruments.server.services.power"
        self.instruments.register_channel_callback(channel, callback)
        stream_num = self.instruments.call(channel, "openStreamForPath:", "live/level.dat").selector
        print("open", stream_num)
        print("start", self.instruments.call(channel, "startStreamTransfer:", float(stream_num)).selector)
        print("[!] wait a few seconds, be patient...")
        while not stopSignal.wait(1):
            pass
        log.info(f"stop{self.instruments.call(channel, 'endStreamTransfer:', float(stream_num)).selector}")

    def xcode_energy(self, pid, stopSignal: threading.Event = threading.Event()):
        """
        get energy
        @param pid:
        @param stopSignal:
        @return:
        """
        self.instruments.call(InstrumentsService.XcodeEnergy, "startSamplingForPIDs:", {pid})
        while not stopSignal.wait(1):
            ret = self.instruments.call(InstrumentsService.XcodeEnergy, "sampleAttributes:forPIDs:", {}, {pid})
            print(ret.selector)

    def get_condition_inducer(self):
        """ Get condition data configuration 获取压力数据配置数据
        :return:
        """
        ret = self.instruments.call(InstrumentsService.ConditionInducer, "availableConditionInducers").selector
        return ret

    def set_condition_inducer(self,
                              condition_identifier,
                              profile_identifier,
                              stopSignal: threading.Event = threading.Event()):
        """ Set mobile phone status, simulated network, mobile cpu pressure, etc; 设置手机状态，模拟网络，手机压力数据等
        @param condition_identifier:
        @param profile_identifier:
        @param stopSignal: thread event control

        :return:
        """
        ret = self.instruments.call(InstrumentsService.ConditionInducer,
                                    'enableConditionWithIdentifier:profileIdentifier:',
                                    condition_identifier, profile_identifier).selector
        log.info(
            f"Condition configuration enabled [{profile_identifier}] successfully, please do not stop the command...")

        while not stopSignal.wait(1):
            pass
        return ret

    def disable_condition_inducer(self):
        """ 关闭手机状态，模拟网络，手机压力数据等
        """
        c = self.instruments.call(InstrumentsService.ConditionInducer, 'disableActiveCondition').selector
        return c

    def xctest(self, bundle_id, USE_PORT='', quit_event=threading.Event()):
        log = Log.getLogger(LOG.xctest.value)

        def _callback(res):
            log.info(f" {res.selector} : {res.auxiliaries}")

        with InstallationProxyService(lockdown=self.lockdown) as install:
            app_info = install.find_bundle_id(bundle_id)
            if not app_info:
                log.warning(f"No app matches {bundle_id}")
                return

        log.info("BundleID: %s", bundle_id)
        log.info("DeviceIdentifier: %s", self.lockdown.device_info.get('UniqueDeviceID'))
        sign_identity = app_info.get("SignerIdentity", "")
        log.info("SignIdentity: %r", sign_identity)
        XCODE_VERSION = 29
        session_identifier = NSUUID(bytes=os.urandom(16), version=4)
        ManagerdLockdown1 = TestManagerdLockdown(self.lockdown).init()

        ManagerdLockdown1.make_channel("dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface")
        if self.lockdown.ios_version > Version('11.0'):
            result = ManagerdLockdown1.call(
                "dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface",
                "_IDE_initiateControlSessionWithProtocolVersion:", RawObj(XCODE_VERSION)).selector
            log.info("result: %s", result)
        ManagerdLockdown1.register_selector_callback(DTXEnum.FINISHED, lambda _: quit_event.set())
        ManagerdLockdown1.register_undefined_callback(_callback)

        ManagerdLockdown2 = TestManagerdLockdown(self.lockdown).init()
        ManagerdLockdown2.make_channel("dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface")
        ManagerdLockdown2.register_selector_callback(DTXEnum.FINISHED, lambda _: quit_event.set())
        ManagerdLockdown2.register_undefined_callback(_callback)

        _start_flag = threading.Event()

        def _start_executing(res=None):
            if _start_flag.is_set():
                return
            _start_flag.set()

            log.info("Start execute test plan with IDE version: %d",
                     XCODE_VERSION)
            ManagerdLockdown2._call(False, 0xFFFFFFFF, '_IDE_startExecutingTestPlanWithProtocolVersion:',
                                    RawObj(XCODE_VERSION))

        def _show_log_message(res):
            log.info(f"{res.selector} : {res.auxiliaries}")
            if 'Received test runner ready reply with error: (null' in ''.join(
                    res.auxiliaries):
                log.info("Test runner ready detected")
                _start_executing()

        ManagerdLockdown2.register_selector_callback('_XCT_testBundleReadyWithProtocolVersion:minimumVersion:',
                                                     _start_executing)
        ManagerdLockdown2.register_selector_callback('_XCT_logDebugMessage:', _show_log_message)
        ManagerdLockdown2.register_selector_callback('_XCT_didFinishExecutingTestPlan', lambda _: quit_event.set())

        result = ManagerdLockdown2.call('dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface',
                                        '_IDE_initiateSessionWithIdentifier:forClient:atPath:protocolVersion:',
                                        RawObj(
                                            session_identifier,
                                            str(session_identifier) + '-6722-000247F15966B083',
                                            '/Applications/Xcode.app/Contents/Developer/usr/bin/xcodebuild',
                                            XCODE_VERSION
                                        )).selector
        log.info("result: %s", result)
        # launch_wda
        xctest_path = "/tmp/WebDriverAgentRunner-" + str(session_identifier).upper() + ".xctestconfiguration"
        xctest_content = archive(XCTestConfiguration({
            "testBundleURL": NSURL(None, "file://" + app_info['Path'] + "/PlugIns/WebDriverAgentRunner.xctest"),
            "sessionIdentifier": session_identifier,
        }))

        fsync = HouseArrestService(self.lockdown)
        fsync.send_command(bundle_id)
        for fname in fsync.read_directory("/tmp"):
            if fname.endswith(".xctestconfiguration"):
                log.debug("remove /tmp/%s", fname)
                fsync.file_remove("/tmp/" + fname)
        fsync.set_file_contents(xctest_path, xctest_content)

        conn = InstrumentServer(self.lockdown).init()
        conn.call('com.apple.instruments.server.services.processcontrol', 'processIdentifierForBundleIdentifier:',
                  bundle_id)

        conn.register_undefined_callback(_callback)
        app_path = app_info['Path']
        app_container = app_info['Container']

        xctestconfiguration_path = app_container + xctest_path
        log.info("AppPath: %s", app_path)
        log.info("AppContainer: %s", app_container)

        app_env = {
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
            'USE_PORT': str(USE_PORT),
        }
        if self.lockdown.ios_version > Version('11.0'):
            app_env['DYLD_INSERT_LIBRARIES'] = '/Developer/usr/lib/libMainThreadChecker.dylib'
            app_env['OS_ACTIVITY_DT_MODE'] = 'YES'
        app_options = {'StartSuspendedKey': False}
        if self.lockdown.ios_version > Version('12.0'):
            app_options['ActivateSuspended'] = True

        app_args = [
            '-NSTreatUnknownArgumentsAsOpen', 'NO',
            '-ApplePersistenceIgnoreState', 'YES'
        ]

        identifier = "launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments:options:"

        pid = conn.call('com.apple.instruments.server.services.processcontrol', identifier,
                        app_path, bundle_id, app_env, app_args, app_options).selector
        if not isinstance(pid, int):
            log.error(f"Launch failed: {pid}")
            raise Exception("Launch failed")

        log.info(f"Launch {bundle_id} pid: {pid}")

        conn.call('com.apple.instruments.server.services.processcontrol', "startObservingPid:", RawObj(pid))

        if quit_event:
            conn.register_selector_callback(DTXEnum.FINISHED, lambda _: quit_event.set())

        if self.lockdown.ios_version > Version('12.0'):
            identifier = '_IDE_authorizeTestSessionWithProcessID:'
            result = ManagerdLockdown1.call(
                'dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface',
                identifier,
                RawObj(pid)).selector
            log.info("_IDE_authorizeTestSessionWithProcessID: %s", result)
        else:
            identifier = '_IDE_initiateControlSessionForTestProcessID:protocolVersion:'
            result = ManagerdLockdown1.call(
                'dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface',
                identifier,
                RawObj(pid), RawObj(XCODE_VERSION)).selector
            log.info("_IDE_authorizeTestSessionWithProcessID: %s", result)

        while not quit_event.wait(.1):
            pass
        log.warning("xctrunner quited")
        conn.stop()
        ManagerdLockdown2.stop()
        ManagerdLockdown1.stop()

    def core_profile(self, config, pid, name, stopSignal: threading.Event = threading.Event()):
        def on_graphics_message(res):
            if type(res.selector) is InstrumentRPCParseError:
                for args in Kperf.to_str(res.selector.data):
                    print(args)

        self.instruments.register_channel_callback("com.apple.instruments.server.services.coreprofilesessiontap",
                                                   on_graphics_message)
        traceCodesFile = self.device_info.traceCodesFile()
        Kperf = KperfData(traceCodesFile, pid, name)
        self.instruments.call("com.apple.instruments.server.services.coreprofilesessiontap", "setConfig:", config)
        self.instruments.call("com.apple.instruments.server.services.coreprofilesessiontap", "start")
        while not stopSignal.wait(1):
            pass
        self.instruments.call("com.apple.instruments.server.services.coreprofilesessiontap", "stop")
        self.instruments.stop()

    def app_launch_lifecycle(self, bundleid, stopSignal: threading.Event = threading.Event()):
        traceCodesFile = self.device_info.traceCodesFile()
        Kperf = KperfData(traceCodesFile)
        machTimeInfo = self.instruments.call("com.apple.instruments.server.services.deviceinfo",
                                             "machTimeInfo").selector
        usecs_since_epoch = self.lockdown.get_value(key='TimeIntervalSince1970') * 1000000
        LifeCycle = AppLifeCycle(machTimeInfo, usecs_since_epoch)
        filter_pid = None

        def demo(data):
            for event in Kperf.to_dict(data):
                if isinstance(event, KdBufParser):
                    _process_name = Kperf.tid_names.get(event.tid)
                    _pid = Kperf.threads_pids.get(event.tid)
                    process_key = (_pid, _process_name)
                    if filter_pid == _pid:
                        if event.class_code in (0x1f, 0x2b, 0x31):
                            LifeCycle.decode_app_lifecycle(event, process_key)
                        if event.debug_id == 835321862:
                            LifeCycle.format_str()
                            stopSignal.set()

        def on_graphics_message(res):
            if type(res.selector) is InstrumentRPCParseError:
                demo(res.selector.data)

        self.instruments.register_channel_callback("com.apple.instruments.server.services.coreprofilesessiontap",
                                                   on_graphics_message)
        self.instruments.call("com.apple.instruments.server.services.coreprofilesessiontap", "setConfig:",
                              {'rp': 100,
                               'bm': 1,
                               'tc': [{'kdf2': {735576064, 19202048, 67895296, 835321856, 735838208, 554762240,
                                                730267648, 520552448, 117440512, 19922944, 17563648, 17104896, 17367040,
                                                771686400, 520617984, 20971520, 520421376},
                                       'csd': 128,
                                       'tk': 3,
                                       'ta': [[3], [0], [2], [1, 1, 0]],
                                       'uuid': str(uuid.uuid4()).upper()}],
                               }, {'tsf': [65537],
                                   'ta': [[0], [2], [1, 1, 0]],
                                   'si': 5000000,
                                   'tk': 1,
                                   'uuid': str(uuid.uuid4()).upper()})
        self.instruments.call("com.apple.instruments.server.services.coreprofilesessiontap", "start")
        channel = "com.apple.instruments.server.services.processcontrol"
        rpc2 = InstrumentServer(lockdown=self.lockdown).init()
        filter_pid = rpc2.call(channel,
                               'launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments:options:',
                               '',
                               bundleid,
                               {'OS_ACTIVITY_DT_MODE': '1',
                                'HIPreventRefEncoding': '1',
                                'DYLD_PRINT_TO_STDERR': '1'}, [],
                               {'StartSuspendedKey': 0}).selector
        print(f'start {bundleid} pid:{filter_pid} [!] wait a few seconds, being analysed...')

        while not stopSignal.wait(1):
            pass
        self.instruments.call("com.apple.instruments.server.services.coreprofilesessiontap", "stop")
        self.instruments.stop()
        rpc2.stop()

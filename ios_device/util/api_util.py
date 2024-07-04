"""
@Date    : 2021-01-28
@Author  : liyachao
"""
import logging
import os
import threading
from packaging.version import Version

from ios_device.util.bpylist2 import NSUUID, XCTestConfiguration, NSURL

from ios_device.servers.Installation import InstallationProxyService
from ios_device.servers.Instrument import InstrumentServer
from ios_device.servers.dvt import DTXEnum
from ios_device.servers.house_arrest import HouseArrestService
from ios_device.servers.testmanagerd import TestManagerdLockdown
from ios_device.util.bpylist2 import archive
from ios_device.util.dtx_msg import RawObj
from ios_device.util.forward import ForwardPorts
from ios_device.util.lockdown import LockdownClient


def channel_validate(channel: InstrumentServer):
    if not channel:
        return False, "The rpc channel is not enabled. Please initialize it first"
    return True, ""


def caller(res, func):
    """
    异步回调中转器
    :param res:
    :param func:
    :return:
    """
    if not isinstance(res, bytes):
        res_dic = dict()
        header = res.selector
        if header:
            res_dic["header"] = header
        body = res.auxiliaries
        if body:
            res_dic["body"] = body
        func(res_dic)
    else:
        func(res)


def network_caller(res, func):
    """
    网络异步回调包解析
    :param res:
    :param func:
    :return:
    """
    from construct import Struct, Int32ul, Bytes, Adapter, Switch, this, Int16ub, Int8ul
    import ipaddress

    class IP(Adapter):
        def _decode(self, obj, context, path):
            return ipaddress.ip_address(obj)

    headers = {
        0: ['InterfaceIndex', "Name"],
        1: ['LocalAddress', 'RemoteAddress', 'InterfaceIndex', 'Pid', 'RecvBufferSize', 'RecvBufferUsed',
            'SerialNumber', 'Kind'],
        2: ['RxPackets', 'RxBytes', 'TxPackets', 'TxBytes', 'RxDups', 'RxOOO', 'TxRetx', 'MinRTT', 'AvgRTT',
            'ConnectionSerial']
    }
    msg_type = {
        0: "interface-detection",
        1: "connection-detected",
        2: "connection-update",
    }

    SockAddr = Struct(
        'len' / Int8ul,
        Int8ul,
        'port' / Int16ub,
        'network' / Switch(this.len, {
            0x1c: Struct(
                Int32ul,
                'address' / IP(Bytes(16)),
                Int32ul, ),
            0x10: Struct(
                'address' / IP(Bytes(4)),
                Bytes(8))})
    )
    data = res.selector
    if data[0] == 1:
        addr = SockAddr.parse(data[1][0])
        data[1][0] = f"{addr.network.address}:{addr.port}"
        addr = SockAddr.parse(data[1][1])
        data[1][1] = f"{addr.network.address}:{addr.port}"

    func({str(msg_type[data[0]]): dict(zip(headers[data[0]], data[1]))})


def system_caller(res, func):
    if isinstance(res.selector, list):
        func(res.selector)


class PyIOSDeviceException(Exception):

    def __init__(self, *args):
        self.args = args


class RunXCUITest(threading.Thread):
    def __init__(self, bundle_id, callback, device_id=None, app_env: dict = None,
                 pair_ports=None):
        super().__init__()
        if pair_ports is None:
            pair_ports = ["8100:8100"]
        self.device_id = device_id
        self.bundle_id = bundle_id
        self.quit_event = threading.Event()
        self.callback = callback
        self.app_env = app_env
        self.lock_down = None
        self.forward = False
        self.pair_ports = pair_ports
        self.forward_thread = None

    def stop(self):
        if self.forward and self.forward_thread:
            self.forward_thread.stop()
        self.quit_event.set()

    def run(self) -> None:
        def _callback(res):
            self.callback(res.auxiliaries)

        lock_down = LockdownClient(udid=self.device_id)
        installation = InstallationProxyService(lockdown=lock_down)

        if self.pair_ports:
            self.forward = True
            self.forward_thread = ForwardPorts(pair_ports=self.pair_ports, device_id=self.device_id)
            self.forward_thread.start()

        app_info = installation.find_bundle_id(self.bundle_id)
        if not app_info:
            raise Exception("No app matches", self.bundle_id)
        logging.debug("BundleID: %s", self.bundle_id)
        logging.debug("DeviceIdentifier: %s", lock_down.device_info.get('UniqueDeviceID'))
        sign_identity = app_info.get("SignerIdentity", "")
        logging.debug("SignIdentity: %r", sign_identity)
        xcode_version = 29
        session_identifier = NSUUID(bytes=os.urandom(16), version=4)
        manager_lock_down_1 = TestManagerdLockdown(lock_down).init()

        manager_lock_down_1.make_channel("dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface")
        if lock_down.ios_version > Version('11.0'):
            result = manager_lock_down_1.call(
                "dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface",
                "_IDE_initiateControlSessionWithProtocolVersion:", RawObj(xcode_version)).selector
            logging.debug("result: %s", result)
        manager_lock_down_1.register_selector_callback(DTXEnum.FINISHED, lambda _: self.quit_event.set())
        manager_lock_down_1.register_undefined_callback(_callback)

        manager_lock_down_2 = TestManagerdLockdown(lock_down).init()
        manager_lock_down_2.make_channel("dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface")
        manager_lock_down_2.register_selector_callback(DTXEnum.FINISHED, lambda _: self.quit_event.set())
        manager_lock_down_2.register_undefined_callback(_callback)

        _start_flag = threading.Event()

        def _start_executing(res=None):
            if _start_flag.is_set():
                return
            _start_flag.set()

            logging.debug(" _start_executing Start execute test plan with IDE version: %d",
                          xcode_version)
            manager_lock_down_2._call(False, 0xFFFFFFFF, '_IDE_startExecutingTestPlanWithProtocolVersion:',
                                      RawObj(xcode_version))

        def _show_log_message(res):
            # logging.info(f"{res.selector} : {get_auxiliary_text(res.raw)}")
            if 'Received test runner ready reply with error: (null' in ''.join(
                    res.auxiliaries):
                logging.debug("_start_executing Test runner ready detected")
                _start_executing()

        manager_lock_down_2.register_selector_callback('_XCT_testBundleReadyWithProtocolVersion:minimumVersion:',
                                                       _start_executing)
        manager_lock_down_2.register_selector_callback('_XCT_logDebugMessage:', _show_log_message)
        manager_lock_down_2.register_selector_callback('_XCT_didFinishExecutingTestPlan',
                                                       lambda _: self.quit_event.set())

        result = manager_lock_down_2.call('dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface',
                                          '_IDE_initiateSessionWithIdentifier:forClient:atPath:protocolVersion:',
                                          RawObj(
                                              session_identifier,
                                              str(session_identifier) + '-6722-000247F15966B083',
                                              '/Applications/Xcode.app/Contents/Developer/usr/bin/xcodebuild',
                                              xcode_version
                                          )).selector
        logging.debug("_start_executing result: %s", result)
        # launch_wda
        xctest_path = "/tmp/WebDriverAgentRunner-" + str(session_identifier).upper() + ".xctestconfiguration"
        xctest_content = archive(XCTestConfiguration({
            "testBundleURL": NSURL(None, "file://" + app_info['Path'] + "/PlugIns/WebDriverAgentRunner.xctest"),
            "sessionIdentifier": session_identifier,
        }))

        fsync = HouseArrestService(lock_down)
        fsync.send_command(self.bundle_id)
        for fname in fsync.read_directory("/tmp"):
            if fname.endswith(".xctestconfiguration"):
                logging.debug("remove /tmp/%s", fname)
                fsync.file_remove("/tmp/" + fname)
        fsync.set_file_contents(xctest_path, xctest_content)

        conn = InstrumentServer(lock_down).init()
        conn.call('com.apple.instruments.server.services.processcontrol', 'processIdentifierForBundleIdentifier:',
                  self.bundle_id)

        conn.register_undefined_callback(_callback)
        app_path = app_info['Path']
        app_container = app_info['Container']

        xctestconfiguration_path = app_container + xctest_path
        logging.debug("AppPath: %s", app_path)
        logging.debug("AppContainer: %s", app_container)

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
            'USE_PORT': '',
        }
        if self.app_env:
            app_env.update(self.app_env)
        if lock_down.ios_version > Version('11.0'):
            app_env['DYLD_INSERT_LIBRARIES'] = '/Developer/usr/lib/libMainThreadChecker.dylib'
            app_env['OS_ACTIVITY_DT_MODE'] = 'YES'
        app_options = {'StartSuspendedKey': False}
        if lock_down.ios_version > Version('12.0'):
            app_options['ActivateSuspended'] = True

        app_args = [
            '-NSTreatUnknownArgumentsAsOpen', 'NO',
            '-ApplePersistenceIgnoreState', 'YES'
        ]

        identifier = "launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments:options:"

        pid = conn.call('com.apple.instruments.server.services.processcontrol', identifier,
                        app_path, self.bundle_id, app_env, app_args, app_options).selector
        if not isinstance(pid, int):
            logging.error(f"Launch failed: {pid}")
            raise Exception("Launch failed")

        logging.debug(f" Launch {self.bundle_id} pid: {pid}")

        conn.call('com.apple.instruments.server.services.processcontrol', "startObservingPid:", RawObj(pid))

        if self.quit_event:
            conn.register_selector_callback(DTXEnum.FINISHED, lambda _: self.quit_event.set())

        if lock_down.ios_version > Version('12.0'):
            identifier = '_IDE_authorizeTestSessionWithProcessID:'
            result = manager_lock_down_1.call(
                'dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface',
                identifier,
                RawObj(pid)).selector
            logging.debug("_IDE_authorizeTestSessionWithProcessID: %s", result)
        else:
            identifier = '_IDE_initiateControlSessionForTestProcessID:protocolVersion:'
            result = manager_lock_down_1.call(
                'dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface',
                identifier,
                RawObj(pid, xcode_version)).selector
            logging.debug("_IDE_authorizeTestSessionWithProcessID: %s", result)

        while not self.quit_event.wait(.1):
            pass
        logging.warning("xctrunner quited")
        conn.stop()
        manager_lock_down_2.stop()
        manager_lock_down_1.stop()

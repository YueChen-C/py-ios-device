"""
@Date    : 2021-01-28
@Author  : liyachao
"""
import logging
import struct
import threading
from _ctypes import Structure
from ctypes import c_byte, c_uint16, c_uint32
from datetime import datetime
from distutils.version import LooseVersion

from numpy import long, mean

from ios_device.servers.house_arrest import HouseArrestClient

from ios_device.util.bpylist import archive

from ios_device.servers.testmanagerd import TestManagerdLockdown

from ios_device.util._types import NSUUID, XCTestConfiguration, NSURL

from ios_device.servers.Installation import InstallationProxy

from ios_device.util.lockdown import LockdownClient

from ios_device.servers.DTXSever import DTXServerRPCResult, DTXServerRPCRawObj, DTXEnum, InstrumentRPCParseError
from ios_device.servers.Instrument import InstrumentServer
from ios_device.util.dtxlib import selector_to_pyobject, get_auxiliary_text
from ios_device.util.utils import kperf_data


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
    if isinstance(res, DTXServerRPCResult):
        res_dic = dict()
        header = selector_to_pyobject(res.raw._selector)
        if header:
            res_dic["header"] = header
        body = get_auxiliary_text(res.raw)
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
    from socket import inet_ntoa, htons, inet_ntop, AF_INET6
    # RxDups : 乱序
    # RxOOO : 丢包
    # TxRetx : 延时

    headers = {
        0: ['InterfaceIndex', "Name"],
        1: ['LocalAddress', 'RemoteAddress', 'InterfaceIndex', 'Pid', 'RecvBufferSize', 'RecvBufferUsed',
            'SerialNumber', 'Kind'],
        2: ['SendPackage', 'SendBytes', 'ReceivePackage', 'ReceiveBytes', 'RepeatPackage', 'DisorderlyPackage',
            'NeedResendPackage', 'MinResponseTime', 'PackageSerialNumber',
            'ConnectionSerial']
    }
    msg_type = {
        0: "interface-detection",
        1: "connection-detected",
        2: "connection-update",
    }

    class SockAddr4(Structure):
        _fields_ = [
            ('len', c_byte),
            ('family', c_byte),
            ('port', c_uint16),
            ('addr', c_byte * 4),
            ('zero', c_byte * 8)
        ]

        def __str__(self):
            return f"{inet_ntoa(self.addr)}:{htons(self.port)}"

    class SockAddr6(Structure):
        _fields_ = [
            ('len', c_byte),
            ('family', c_byte),
            ('port', c_uint16),
            ('flowinfo', c_uint32),
            ('addr', c_byte * 16),
            ('scopeid', c_uint32)
        ]

        def __str__(self):
            return f"[{inet_ntop(AF_INET6, self.addr)}]:{htons(self.port)}"

    data = res.parsed
    if data[0] == 1:
        if len(data[1][0]) == 16:
            data[1][0] = str(SockAddr4.from_buffer_copy(data[1][0]))
            data[1][1] = str(SockAddr4.from_buffer_copy(data[1][1]))
        elif len(data[1][0]) == 28:
            data[1][0] = str(SockAddr6.from_buffer_copy(data[1][0]))
            data[1][1] = str(SockAddr6.from_buffer_copy(data[1][1]))
    func({str(msg_type[data[0]]): dict(zip(headers[data[0]], data[1]))})


def power_caller(res, func):
    """
    电量异步回调包解析
    :param res:
    :param func:
    :return:
    """
    headers = ['startingTime', 'duration', 'level']  # DTPower
    ctx = {
        'remained': b''
    }
    ctx['remained'] += res.parsed['data']
    cur = 0
    while cur + 3 * 8 <= len(ctx['remained']):
        print("[level.dat]", dict(zip(headers, struct.unpack('>ddd', ctx['remained'][cur: cur + 3 * 8]))))
        cur += 3 * 8
        pass
    ctx['remained'] = ctx['remained'][cur:]
    func(ctx)


def system_caller(res, func):
    if isinstance(res.parsed, list):
        func(res.parsed)


class PyIOSDeviceException(Exception):

    def __init__(self, *args):
        self.args = args


class RunXCUITest(threading.Thread):
    def __init__(self, bundle_id, callback, device_id=None, app_env: dict = None):
        super().__init__()
        self.device_id = device_id
        self.bundle_id = bundle_id
        self.quit_event = threading.Event()
        self.callback = callback
        self.app_env = app_env

    def stop(self):
        self.quit_event.set()

    def run(self) -> None:
        def _callback(res):
            self.callback(get_auxiliary_text(res.raw))

        lock_down = LockdownClient(udid=self.device_id)
        installation = InstallationProxy(lockdown=lock_down)
        app_info = installation.find_bundle_id(self.bundle_id)
        if not app_info:
            raise Exception("No app matches", self.bundle_id)
        logging.info("BundleID: %s", self.bundle_id)
        logging.info("DeviceIdentifier: %s", lock_down.device_info.get('UniqueDeviceID'))
        sign_identity = app_info.get("SignerIdentity", "")
        logging.info("SignIdentity: %r", sign_identity)
        xcode_version = 29
        session_identifier = NSUUID('96508379-4d3b-4010-87d1-6483300a7b76')
        manager_lock_down_1 = TestManagerdLockdown(lock_down).init()

        manager_lock_down_1._make_channel("dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface")
        if lock_down.ios_version > LooseVersion('11.0'):
            result = manager_lock_down_1.call(
                "dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface",
                "_IDE_initiateControlSessionWithProtocolVersion:", DTXServerRPCRawObj(xcode_version)).parsed
            logging.info("result: %s", result)
        manager_lock_down_1.register_callback(DTXEnum.FINISHED, lambda _: self.quit_event.set())
        manager_lock_down_1.register_unhandled_callback(_callback)

        manager_lock_down_2 = TestManagerdLockdown(lock_down).init()
        manager_lock_down_2._make_channel("dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface")
        manager_lock_down_2.register_callback(DTXEnum.FINISHED, lambda _: self.quit_event.set())
        manager_lock_down_2.register_unhandled_callback(_callback)

        _start_flag = threading.Event()

        def _start_executing(res=None):
            if _start_flag.is_set():
                return
            _start_flag.set()

            logging.info(" _start_executing Start execute test plan with IDE version: %d",
                         xcode_version)
            manager_lock_down_2._call(False, 0xFFFFFFFF, '_IDE_startExecutingTestPlanWithProtocolVersion:',
                                      DTXServerRPCRawObj(xcode_version))

        def _show_log_message(res):
            logging.info(f"{res.parsed} : {get_auxiliary_text(res.raw)}")
            if 'Received test runner ready reply with error: (null' in ''.join(
                    get_auxiliary_text(res.raw)):
                logging.info("_start_executing Test runner ready detected")
                _start_executing()

        manager_lock_down_2.register_callback('_XCT_testBundleReadyWithProtocolVersion:minimumVersion:',
                                              _start_executing)
        manager_lock_down_2.register_callback('_XCT_logDebugMessage:', _show_log_message)
        manager_lock_down_2.register_callback('_XCT_didFinishExecutingTestPlan', lambda _: self.quit_event.set())

        result = manager_lock_down_2.call('dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface',
                                          '_IDE_initiateSessionWithIdentifier:forClient:atPath:protocolVersion:',
                                          DTXServerRPCRawObj(
                                              session_identifier,
                                              str(session_identifier) + '-6722-000247F15966B083',
                                              '/Applications/Xcode.app/Contents/Developer/usr/bin/xcodebuild',
                                              xcode_version
                                          )).parsed
        logging.info("_start_executing result: %s", result)
        # launch_wda
        xctest_path = "/tmp/WebDriverAgentRunner-" + str(session_identifier).upper() + ".xctestconfiguration"
        xctest_content = archive(XCTestConfiguration({
            "testBundleURL": NSURL(None, "file://" + app_info['Path'] + "/PlugIns/WebDriverAgentRunner.xctest"),
            "sessionIdentifier": session_identifier,
        }))

        fsync = HouseArrestClient(udid=self.device_id)
        fsync.send_command(self.bundle_id)
        for fname in fsync.read_directory("/tmp"):
            if fname.endswith(".xctestconfiguration"):
                logging.debug("remove /tmp/%s", fname)
                fsync.file_remove("/tmp/" + fname)
        fsync.set_file_contents(xctest_path, xctest_content)

        conn = InstrumentServer(lock_down).init()
        conn.call('com.apple.instruments.server.services.processcontrol', 'processIdentifierForBundleIdentifier:',
                  self.bundle_id)

        conn.register_unhandled_callback(_callback)
        app_path = app_info['Path']
        app_container = app_info['Container']

        xctestconfiguration_path = app_container + xctest_path
        logging.info("AppPath: %s", app_path)
        logging.info("AppContainer: %s", app_container)

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
        if lock_down.ios_version > LooseVersion('11.0'):
            app_env['DYLD_INSERT_LIBRARIES'] = '/Developer/usr/lib/libMainThreadChecker.dylib'
            app_env['OS_ACTIVITY_DT_MODE'] = 'YES'
        app_options = {'StartSuspendedKey': False}
        if lock_down.ios_version > LooseVersion('12.0'):
            app_options['ActivateSuspended'] = True

        app_args = [
            '-NSTreatUnknownArgumentsAsOpen', 'NO',
            '-ApplePersistenceIgnoreState', 'YES'
        ]

        identifier = "launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments:options:"

        pid = conn.call('com.apple.instruments.server.services.processcontrol', identifier,
                        app_path, self.bundle_id, app_env, app_args, app_options).parsed
        if not isinstance(pid, int):
            logging.error(f"Launch failed: {pid}")
            raise Exception("Launch failed")

        logging.info(f" Launch {self.bundle_id} pid: {pid}")

        conn.call('com.apple.instruments.server.services.processcontrol', "startObservingPid:", DTXServerRPCRawObj(pid))

        if self.quit_event:
            conn.register_callback(DTXEnum.FINISHED, lambda _: self.quit_event.set())

        if lock_down.ios_version > LooseVersion('12.0'):
            identifier = '_IDE_authorizeTestSessionWithProcessID:'
            result = manager_lock_down_1.call(
                'dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface',
                identifier,
                DTXServerRPCRawObj(pid)).parsed
            logging.info("_IDE_authorizeTestSessionWithProcessID: %s", result)
        else:
            identifier = '_IDE_initiateControlSessionForTestProcessID:protocolVersion:'
            result = manager_lock_down_1.call(
                'dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface',
                identifier,
                DTXServerRPCRawObj(pid, xcode_version)).parsed
            logging.info("_IDE_authorizeTestSessionWithProcessID: %s", result)

        while not self.quit_event.wait(.1):
            pass
        logging.warning("xctrunner quited")
        conn.stop()
        manager_lock_down_2.stop()
        manager_lock_down_1.stop()

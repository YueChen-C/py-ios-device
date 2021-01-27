import logging
import threading
from distutils.version import LooseVersion

from servers.DTXSever import DTXServerRPCRawObj
from servers.Instrument import InstrumentServer
from servers.house_arrest import HouseArrestClient
from servers.installation_proxy import installation_proxy
from servers.testmanagerd import TestManagerdLockdown
from util.bpylist.archiver import archive
from util.bpylist.bplistlib._types import XCTestConfiguration, NSURL, NSUUID
from util.dtxlib import get_auxiliary_text
from util.lockdown import LockdownClient


class RunXCUITest:
    def __init__(self, bundle_id, udid=None):
        self.udid = udid
        self.bundle_id = bundle_id

    def start(self):
        self.lockdown = LockdownClient(udid=self.udid)
        installation = installation_proxy(lockdown=self.lockdown)
        app_info = installation.find_bundle_id(self.bundle_id)
        if not app_info:
            raise Exception("No app matches", self.bundle_id)
        logging.info("BundleID: %s", self.bundle_id)
        logging.info("DeviceIdentifier: %s", self.lockdown.device_info.get('UniqueDeviceID'))
        sign_identity = app_info.get("SignerIdentity", "")
        logging.info("SignIdentity: %r", sign_identity)
        XCODE_VERSION = 29
        session_identifier = NSUUID('96508379-4d3b-4010-87d1-6483300a7b76')
        ManagerdLockdown1 = TestManagerdLockdown(self.lockdown).init()
        done = threading.Event()

        ManagerdLockdown1.register_callback("_notifyOfPublishedCapabilities:", lambda _: done.set())
        ManagerdLockdown1.start()
        if not done.wait(5):
            logging.debug("[WARN] timeout waiting capabilities")
        quit_event = threading.Event()

        ManagerdLockdown1._make_channel("dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface")
        if self.lockdown.ios_version > LooseVersion('11.0'):
            result = ManagerdLockdown1.call(
                "dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface",
                "_IDE_initiateControlSessionWithProtocolVersion:", DTXServerRPCRawObj(XCODE_VERSION)).parsed
            logging.info("result: %s", result)
        ManagerdLockdown1.register_callback(":finished:", lambda _: quit_event.set())

        ManagerdLockdown2 = TestManagerdLockdown(self.lockdown).init()
        done = threading.Event()
        ManagerdLockdown2.register_callback("_notifyOfPublishedCapabilities:", lambda _: done.set())
        ManagerdLockdown2.start()
        if not done.wait(5):
            logging.debug("[WARN] timeout waiting capabilities")

        ManagerdLockdown2._make_channel("dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface")

        ManagerdLockdown2.register_callback(":finished:", lambda _: quit_event.set())

        _start_flag = threading.Event()

        def _start_executing(res=None):
            if _start_flag.is_set():
                return
            _start_flag.set()

            logging.info("Start execute test plan with IDE version: %d",
                         XCODE_VERSION)
            ManagerdLockdown2._call(False, 0xFFFFFFFF, '_IDE_startExecutingTestPlanWithProtocolVersion:',
                                    DTXServerRPCRawObj(XCODE_VERSION))

        def _show_log_message(res):
            logging.info(f"{res.parsed} : {get_auxiliary_text(res.raw)}")
            if 'Received test runner ready reply with error: (null' in ''.join(
                    res.parsed):
                logging.info("Test runner ready detected")
                _start_executing()

        ManagerdLockdown2.register_callback('_XCT_testBundleReadyWithProtocolVersion:minimumVersion:', _start_executing)
        ManagerdLockdown2.register_callback('_XCT_logDebugMessage:', _show_log_message)

        result = ManagerdLockdown2.call('dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface',
                                        '_IDE_initiateSessionWithIdentifier:forClient:atPath:protocolVersion:',
                                        DTXServerRPCRawObj(
                                            session_identifier,
                                            str(session_identifier) + '-6722-000247F15966B083',
                                            '/Applications/Xcode.app/Contents/Developer/usr/bin/xcodebuild',
                                            XCODE_VERSION
                                            )).parsed
        logging.info("result: %s", result)
        # launch_wda
        xctest_path = "/tmp/WebDriverAgentRunner-" + str(session_identifier).upper() + ".xctestconfiguration"
        xctest_content = archive(XCTestConfiguration({
            "testBundleURL": NSURL(None, "file://" + app_info['Path'] + "/PlugIns/WebDriverAgentRunner.xctest"),
            "sessionIdentifier": session_identifier,
        }))

        fsync = HouseArrestClient()
        fsync.send_command(self.bundle_id)
        for fname in fsync.read_directory("/tmp"):
            if fname.endswith(".xctestconfiguration"):
                logging.debug("remove /tmp/%s", fname)
                fsync.remove_directory("/tmp/" + fname)
        fsync.set_file_contents(xctest_path, xctest_content)

        conn = InstrumentServer(self.lockdown).init()
        done = threading.Event()
        conn.register_callback("_notifyOfPublishedCapabilities:", lambda _: done.set())
        conn.start()
        if not done.wait(5):
            logging.debug("[WARN] timeout waiting capabilities")
        conn.call('com.apple.instruments.server.services.processcontrol', 'processIdentifierForBundleIdentifier:',
                  self.bundle_id)

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
        if self.lockdown.ios_version > LooseVersion('11.0'):
            app_env['DYLD_INSERT_LIBRARIES'] = '/Developer/usr/lib/libMainThreadChecker.dylib'
            app_env['OS_ACTIVITY_DT_MODE'] = 'YES'
        app_options = {'StartSuspendedKey': False}
        if self.lockdown.ios_version > LooseVersion('12.0'):
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

        logging.info(f"Launch {self.bundle_id} pid: {pid}")

        conn.call('com.apple.instruments.server.services.processcontrol', "startObservingPid:", DTXServerRPCRawObj(pid))

        def _callback(res):
            logging.info(f" {res.parsed} : {get_auxiliary_text(res.raw)}")

        conn.register_callback('outputReceived:fromProcess:atTime:', _callback)
        if quit_event:
            conn.register_callback(':finished:', lambda _: quit_event.set())

        if self.lockdown.ios_version > LooseVersion('12.0'):
            identifier = '_IDE_authorizeTestSessionWithProcessID:'
            result = ManagerdLockdown1.call(
                'dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface',
                identifier,
                DTXServerRPCRawObj(pid)).parsed
            logging.info("_IDE_authorizeTestSessionWithProcessID: %s", result)
        else:
            identifier = '_IDE_initiateControlSessionForTestProcessID:protocolVersion:'
            result = ManagerdLockdown1.call(
                'dtxproxy:XCTestManager_IDEInterface:XCTestManager_DaemonConnectionInterface',
                identifier,
                DTXServerRPCRawObj(pid, XCODE_VERSION)).parsed
            logging.info("_IDE_authorizeTestSessionWithProcessID: %s", result)

        while not quit_event.wait(.1):
            pass
        logging.warning("xctrunner quited")


if __name__ == '__main__':
    bundle_id = 'com.facebook.wda.WebDriverAgent.Runner'
    RunXCUITest(bundle_id).start()

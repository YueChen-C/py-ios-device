import os
import sys
import time
import uuid

from ios_device.util.lockdown import LockdownClient

sys.path.append(os.getcwd())

from ios_device.cli.base import InstrumentDeviceInfo
from ios_device.servers.Instrument import InstrumentServer
from ios_device.util.lifecycle import AppLifeCycle
from ios_device.util.exceptions import InstrumentRPCParseError
from ios_device.util.kperf_data import KperfData, KdBufParser

index = 11


def app_launch_lifecyle(rpc, bundleid, rsd):
    traceCodesFile = InstrumentDeviceInfo(rpc).traceCodesFile()
    Kperf = KperfData(traceCodesFile)
    machTimeInfo = rpc.call("com.apple.instruments.server.services.deviceinfo",
                            "machTimeInfo").selector
    usecs_since_epoch = rpc.lockdown.get_value(key='TimeIntervalSince1970') * 1000000
    LifeCycle = AppLifeCycle(machTimeInfo, usecs_since_epoch)
    filter_pid = None

    def process_name(pid):
        return Kperf.pid_names.get(pid) or Kperf.tid_names.get(pid)

    def demo(data):
        for event in Kperf.to_dict(data):
            if not isinstance(event, KdBufParser):
                continue
            _pid = Kperf.threads_pids.get(event.tid)
            if _pid is None:
                continue
            # Returns True when the launch sequence completed; the modeler picks
            # the launch events itself, so no class filter is needed here.
            if LifeCycle.decode_app_lifecycle(event, _pid):
                LifeCycle.format_str(describe=process_name)

    def on_graphics_message(res):
        if type(res.selector) is InstrumentRPCParseError:
            demo(res.selector.data)

    rpc.register_channel_callback("com.apple.instruments.server.services.coreprofilesessiontap",
                                  on_graphics_message)
    rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "setConfig:",
             {'rp': 100,
              'bm': 1,
              'tc': [{'kdf2': {735576064, 19202048, 67895296, 835321856, 735838208, 554762240,
                               730267648, 520552448, 117440512, 19922944, 17563648, 17104896,
                               17367040,
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
    rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "start")
    channel = "com.apple.instruments.server.services.processcontrol"
    rpc1 = InstrumentServer(udid='00008030-001A690E2EC3802E').init()
    filter_pid = rpc1.call(channel,
                           'launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments:options:',
                           '',
                           bundleid,
                           {'OS_ACTIVITY_DT_MODE': '1', 'HIPreventRefEncoding': '1',
                            'DYLD_PRINT_TO_STDERR': '1'}, [],
                           {'StartSuspendedKey': 0}).selector
    print(f'start {bundleid} pid:{filter_pid}')

    time.sleep(1000)
    rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "stop")
    LifeCycle.format_str(describe=process_name)  # flush phases that never received an END event
    rpc.stop()
    rpc1.stop()


if __name__ == '__main__':
    # with RemoteLockdownClient(('fd19:a0e8:85d2::1', 53449)) as rsd:
    #     # print(f'start {bundleid}')
    #     rpc = InstrumentServer(rsd).init()
    #     app_launch_lifecyle(rpc, 'com.apple.MobileSMS', rsd)
    #     rpc.stop()

    rpc = InstrumentServer(udid='00008030-001A690E2EC3802E').init()
    app_launch_lifecyle(rpc, 'com.apple.MobileSMS', None)
    rpc.stop()

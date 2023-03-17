import os
import sys
import time
import uuid

sys.path.append(os.getcwd())

from ios_device.cli.base import InstrumentDeviceInfo
from ios_device.servers.Instrument import InstrumentServer
from ios_device.util.lifecycle import AppLifeCycle
from ios_device.util.exceptions import InstrumentRPCParseError
from ios_device.util.kperf_data import KperfData, KdBufParser

index = 11


def app_launch_lifecyle(rpc, bundleid):
    traceCodesFile = InstrumentDeviceInfo(rpc).traceCodesFile()
    Kperf = KperfData(traceCodesFile)
    machTimeInfo = rpc.call("com.apple.instruments.server.services.deviceinfo", "machTimeInfo").selector
    usecs_since_epoch = rpc.lockdown.get_value(key='TimeIntervalSince1970') * 1000000
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

    def on_graphics_message(res):
        if type(res.selector) is InstrumentRPCParseError:
            demo(res.selector.data)

    rpc.register_channel_callback("com.apple.instruments.server.services.coreprofilesessiontap", on_graphics_message)
    rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "setConfig:",
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
    rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "start")
    channel = "com.apple.instruments.server.services.processcontrol"
    rpc1 = InstrumentServer().init()
    filter_pid = rpc1.call(channel,
                           'launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments:options:',
                           '',
                           bundleid,
                           {'OS_ACTIVITY_DT_MODE': '1', 'HIPreventRefEncoding': '1', 'DYLD_PRINT_TO_STDERR': '1'}, [],
                           {'StartSuspendedKey': 0}).selector
    print(f'start {bundleid} pid:{filter_pid}')

    time.sleep(1000)
    rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "stop")
    rpc.stop()
    rpc1.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    app_launch_lifecyle(rpc, 'rn.notes.best')
    rpc.stop()

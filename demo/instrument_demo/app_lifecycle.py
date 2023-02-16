import time
import uuid

from ios_device.cli.base import InstrumentDeviceInfo
from ios_device.servers.Instrument import InstrumentServer
from ios_device.util.lifecycle import AppLifeCycle
from ios_device.util.dtx_msg import RawObj
from ios_device.util.exceptions import InstrumentRPCParseError
from ios_device.util.kperf_data import KperfData, KdBufParser


def app_launch_lifecyle(rpc, bundleid):
    traceCodesFile = InstrumentDeviceInfo(rpc).traceCodesFile()
    Kperf = KperfData(traceCodesFile)
    machTimeInfo = rpc.call("com.apple.instruments.server.services.deviceinfo", "machTimeInfo").selector
    usecs_since_epoch = rpc.lockdown.get_value(key='TimeIntervalSince1970') * 1000000
    LifeCycle = AppLifeCycle(machTimeInfo, usecs_since_epoch)

    def demo(data):
        for event in Kperf.to_dict(data):
            if isinstance(event, KdBufParser):
                _, process_name = Kperf.threads_pids.get(event.tid, (None, None))
                if event.class_code in (0x1f, 0x2b, 0x31) and process_name not in ('SpringBoard',):
                    LifeCycle.decode_app_lifecycle(event, process_name or event.tid)
                if event.debug_id == 835321862:
                    LifeCycle.format_str()

    def on_graphics_message(res):
        if type(res.selector) is InstrumentRPCParseError:
            demo(res.selector.data)

    rpc.register_channel_callback("com.apple.instruments.server.services.coreprofilesessiontap", on_graphics_message)
    rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "setConfig:",
             {'rp': 100,
              'bm': 1,
              'tc': [{'kdf2': {735576064, 835321856, 735838208, 730267648,
                               520552448},
                      'csd': 128,
                      'tk': 3,
                      'ta': [[3], [0], [2], [1, 1, 0]],
                      'uuid': str(uuid.uuid4()).upper()}],
              })
    rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "start")
    channel = "com.apple.instruments.server.services.processcontrol"
    pid = rpc.call(channel, 'launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments:options:',
                    '',
                    bundleid,
                    {'OS_ACTIVITY_DT_MODE': '1', 'HIPreventRefEncoding': '1', 'DYLD_PRINT_TO_STDERR': '1'}, [],
                    {'StartSuspendedKey': 0}).selector
    print(f'start {bundleid} pid:{pid}')

    time.sleep(1000)
    rpc.call("com.apple.instruments.server.services.coreprofilesessiontap", "stop")
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    app_launch_lifecyle(rpc, 'cn.rongcloud.im')
    rpc.stop()

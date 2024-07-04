import dataclasses
import json
import signal
import threading
import uuid
from copy import deepcopy
from datetime import datetime
from packaging.version import Version
from statistics import mean

import click

from ios_device.cli.base import InstrumentsBase
from ios_device.cli.cli import Command, print_json
from ios_device.util import Log, api_util
from ios_device.util.exceptions import InstrumentRPCParseError
from ios_device.util.gpu_decode import JSEvn, TraceData, GRCDecodeOrder, GRCDisplayOrder
from ios_device.util.kc_data import kc_data_parse
from ios_device.util.kperf_data import kdbg_extract_all
from ios_device.util.utils import DumpDisk, DumpNetwork, DumpMemory, convertBytes, \
    MOVIE_FRAME_COST, NANO_SECOND, kperf_data
from ios_device.util.variables import LOG, InstrumentsService

log = Log.getLogger(LOG.Instrument.value)


@click.group()
def cli():
    """ instruments cli """


@cli.group(short_help='run instruments service')
def instruments():
    """
    运行 instruments 组件相关服务

    run instruments service
    """


@instruments.command('runningProcesses', cls=Command, short_help='Show running process list')
def cmd_running_processes(udid, network, format):
    """
    显示正在运行的进程信息

    Show running process list
     """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        processes = rpc.device_info.runningProcesses()
        print_json(processes, format)


@instruments.command('applist', cls=Command)
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId to filter')
def cmd_application(udid, network, format, bundle_id):
    """ Show application list """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        apps = rpc.application_listing(bundle_id)
        print_json(apps, format)


@instruments.command('kill', cls=Command)
@click.option('-p', '--pid', type=click.INT, default=None, help='Process ID to filter')
@click.option('-n', '--name', default=None, help='Process app name to filter')
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId to filter')
def cmd_kill(udid, network, format, pid, name, bundle_id):
    """ Kill a process by its pid. """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        if bundle_id or name:
            pid = rpc.get_pid(bundle_id, name)
        if not pid:
            log.error(f'The pid: {pid} did not start. Try "-h or --help" for help')
            return
        rpc.kill_app(pid)
        print(f'Kill {pid} ...')


@instruments.command('launch', cls=Command)
@click.option('--bundle_id', default=None, help='Process app bundleId to filter')
@click.option('--app_env', default=None, help='App launch environment variable')
def cmd_launch(udid, network, format, bundle_id: str, app_env: dict):
    """
    Launch a process.
    :param bundle_id: Arguments of process to launch, the first argument is the bundle id.
    :param app_env: App launch environment variable
    """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        pid = rpc.launch_app(bundle_id=bundle_id, app_env=app_env)
        print(f'Process launched with pid {pid}')


@instruments.group('information')
def information():
    """ System information. """


@information.command('system', cls=Command)
def cmd_information_system(udid, network, format):
    """ Print system information. """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        print_json(rpc.device_info.systemInformation(), format)


@information.command('hardware', cls=Command)
def cmd_information_hardware(udid, network, format):
    """ Print hardware information. """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        print_json(rpc.device_info.hardwareInformation(), format)


@information.command('network', cls=Command)
def cmd_information_network(udid, network, format):
    """ Print network information. """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        print_json(rpc.device_info.networkInformation(), format)


@instruments.command('xcode_energy', cls=Command)
@click.option('-p', '--pid', type=click.INT, default=None, help='Process ID to filter')
@click.option('-n', '--name', default=None, help='Process app name to filter')
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId to filter')
def cmd_xcode_energy(udid, network, pid, name, bundle_id, format):
    """ Print process about current network activity.  """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        if bundle_id or name:
            pid = rpc.get_pid(bundle_id, name)
        if not pid:
            log.error(f'The pid: {pid} did not start. Try "--help" for help')
            return
        rpc.xcode_energy(pid)


@instruments.command('network_process', cls=Command)
@click.option('-p', '--pid', type=click.INT, default=None, help='Process ID to filter')
@click.option('-n', '--name', default=None, help='Process app name to filter')
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId to filter')
def cmd_network_process(udid, network, pid, name, bundle_id, format):
    """ Print process about current network activity.  """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        if bundle_id or name:
            pid = rpc.get_pid(bundle_id, name)
        if not pid:
            log.error(f'The pid: {pid} did not start. Try "--help" for help')
            return
        rpc.xcode_network(pid)


@instruments.command('networking', cls=Command)
def cmd_networking(udid, network, format):
    """ Print information about current network activity. """

    def _callback(res):
        api_util.network_caller(res, print_json)

    with InstrumentsBase(udid=udid, network=network) as rpc:
        rpc.networking(_callback)


@instruments.command('appmonitor', cls=Command)
@click.option('-t', '--time', type=click.INT, default=1000, help='Output interval time (ms)')
@click.option('-b', '--bundle_id', required=True, help='Process app bundleId to filter')
def cmd_appmonitor(udid, network, format, time, bundle_id):
    """ Get application performance data """
    proc_filter = ['Pid', 'Name', 'CPU', 'Memory', 'DiskReads', 'DiskWrites', 'Threads']
    process_attributes = dataclasses.make_dataclass('SystemProcessAttributes', proc_filter)
    ios_version = Version('0')

    def on_callback_message(res):
        if isinstance(res.selector, list):
            for index, row in enumerate(res.selector):
                if 'Processes' in row:
                    for _pid, process in row['Processes'].items():
                        attrs = process_attributes(*process)
                        if name and attrs.Name != name:
                            continue
                        if not attrs.CPU:
                            attrs.CPU = 0
                        if ios_version < Version('14.0'):
                            attrs.CPU = attrs.CPU * 40
                        attrs.CPU = f'{round(attrs.CPU, 2)} %'
                        attrs.Memory = convertBytes(attrs.Memory)
                        attrs.DiskReads = convertBytes(attrs.DiskReads)
                        attrs.DiskWrites = convertBytes(attrs.DiskWrites)
                        print_json(attrs.__dict__, format)

    with InstrumentsBase(udid=udid, network=network) as rpc:
        ios_version = rpc.lockdown.ios_version
        rpc.process_attributes = ['pid', 'name', 'cpuUsage', 'physFootprint',
                                  'diskBytesRead', 'diskBytesWritten', 'threadCount']
        if bundle_id:
            app = rpc.application_listing(bundle_id)
            if not app:
                print(f"not find {bundle_id}")
                return
            name = app.get('ExecutableName')
        rpc.sysmontap(on_callback_message, time)


@instruments.command('sysmontap', cls=Command)
@click.option('-t', '--time', type=click.INT, default=1000, help='Output interval time (ms)')
@click.option('-p', '--pid', type=click.INT, default=None, help='Process ID to filter')
@click.option('-n', '--name', default=None, help='Process app name to filter')
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId to filter.Omit show all')
@click.option('--processes', is_flag=True, help='Only output process information')
@click.option('--sort', help='Process field sorting')
@click.option('--proc_filter', help='Process param to filter split by ",". Omit show all')
@click.option('--sys_filter', help='System param to filter split by ",". Omit show all')
def cmd_sysmontap(udid, network, format, time, pid, name, bundle_id, processes, sort, proc_filter,
                  sys_filter):
    """ Get more performance data """

    def on_callback_message(res):
        if isinstance(res.selector, list):
            data = deepcopy(res.selector)
            processes_data = {}
            for index, row in enumerate(res.selector):
                if 'Processes' in row:
                    data[index]['Processes'] = {}
                    for _pid, process in row['Processes'].items():
                        process_attributes = dataclasses.make_dataclass('SystemProcessAttributes',
                                                                        proc_filter or rpc.process_attributes)
                        attrs = process_attributes(*process)
                        if pid and pid != _pid:
                            continue
                        if name and attrs.name != name:
                            continue
                        if processes:
                            processes_data[f'{attrs.name}'] = attrs.__dict__
                            continue
                        data[index]['Processes'][f'{attrs.name}'] = attrs.__dict__
                    data[index]['Processes'] = sorted(data[index]['Processes'].items(),
                                                      key=lambda d: d[1].get(sort, 0),
                                                      reverse=True)

                if 'System' in row:
                    if 'SystemAttributes' in data[index]:
                        del data[index]['SystemAttributes']
                    if 'ProcessesAttributes' in data[index]:
                        del data[index]['ProcessesAttributes']
                    data[index]['System'] = dict(zip(rpc.system_attributes, row['System']))
            if processes:
                processes_data = sorted(processes_data.items(), key=lambda d: d[1].get(sort, 0) or 0,
                                        reverse=True)
                print_json(processes_data, format)
            else:
                print_json(data, format)

    with InstrumentsBase(udid=udid, network=network) as rpc:

        if proc_filter:
            data = rpc.device_info.sysmonProcessAttributes()
            proc_filter = proc_filter.split(',')
            proc_filter.extend(['name', 'pid'])
            proc_filter = list(set(proc_filter))
            for proc in proc_filter:
                if proc not in data:
                    log.warn(f'{proc_filter} value：{proc} not in {data}')
                    return
            rpc.process_attributes = proc_filter

        if sys_filter:
            data = rpc.device_info.sysmonSystemAttributes()
            sys_filter = sys_filter.split(',')
            for sys in sys_filter:
                if sys not in data:
                    log.warn(f'{sys_filter} value：{sys} not in {data}')
                    return
            rpc.system_attributes = sys_filter

        if bundle_id:
            app = rpc.application_listing(bundle_id)
            if not app:
                print(f"not find {bundle_id}")
            name = app.get('ExecutableName')
        rpc.sysmontap(on_callback_message, time)


@instruments.command('monitor', cls=Command)
@click.option('--filter', default="all", type=click.Choice(["all", 'disk', 'network', 'memory', 'cpu']), help='')
def cmd_monitor(udid, network, format, filter: str):
    """ Get monitor performance data """
    disk = DumpDisk()
    Network = DumpNetwork()
    Memory = DumpMemory()

    def on_callback_message(res):
        data = {}
        SystemCPUUsage = {}
        if isinstance(res.selector, list):
            for index, row in enumerate(res.selector):
                if 'System' in row:
                    data = dict(zip(rpc.system_attributes, row['System']))
                if "SystemCPUUsage" in row:
                    SystemCPUUsage = row["SystemCPUUsage"]
            if not data:
                return
            if 'disk' == filter.lower():
                print("Disk    >>", disk.decode(data))
            if 'network' == filter.lower():
                print("Network >>", Network.decode(data))
            if 'memory' == filter.lower():
                print("Memory  >>", Memory.decode(data))
            if 'cpu' == filter.lower():
                print("CPU     >>", SystemCPUUsage)
            if "all" == filter.lower():
                print("Memory  >>", Memory.decode(data))
                print("Network >>", Network.decode(data))
                print("Disk    >>", disk.decode(data))
                print("CPU     >>", SystemCPUUsage)

    with InstrumentsBase(udid=udid, network=network) as rpc:
        rpc.process_attributes = ['name', 'pid']
        rpc.system_attributes = rpc.device_info.sysmonSystemAttributes()
        rpc.sysmontap(on_callback_message)


@instruments.group()
def condition():
    """
    Set system running condition
    """


@condition.command('get', cls=Command)
def cmd_get_condition_inducer(udid, network, format):
    """ get aLL condition inducer configuration
    """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        ret = rpc.get_condition_inducer()
        print_json(ret, format)


@condition.command('set', cls=Command)
@click.option('-c', '--condition_id', default=None, help='Process app bundleId to filter')
@click.option('-p', '--profile_id', default='', help='start wda port')
def cmd_set_condition_inducer(udid, network, format, condition_id, profile_id):
    """ set condition inducer
    """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        ret = rpc.set_condition_inducer(condition_id, profile_id)
        print_json(ret, format)


@instruments.command('xcuitest', cls=Command)
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId to filter')
@click.option('-p', '--port', default='', help='start wda port')
def cmd_xcuitest(udid, network, format, bundle_id, port):
    """ Run XCTest required WDA installed.
    """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        rpc.xctest(bundle_id, port)


@instruments.command('fps', cls=Command)
@click.option('-t', '--time', type=click.INT, default=1000, help='Output interval time (ms)')
def cmd_graphics(udid, network, format, time):
    """ Get graphics fps
    """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        def on_callback_message(res):
            data = res.selector
            print_json({"currentTime": str(datetime.now()), "fps": data['CoreAnimationFramesPerSecond']}, format)

        rpc.graphics(on_callback_message, time)


@instruments.command('display', cls=Command)
def cmd_display(udid, network, format):
    """ Get graphics fps
    """
    last_frame = None
    last_1_frame_cost, last_2_frame_cost, last_3_frame_cost = 0, 0, 0
    jank_count = 0
    big_jank_count = 0
    jank_time_count = 0
    mach_time_factor = 125 / 3
    frame_count = 0
    time_count = 0
    last_time = datetime.now().timestamp()
    _list = []

    def on_graphics_message(res):
        nonlocal frame_count, last_frame, last_1_frame_cost, last_2_frame_cost, last_3_frame_cost, time_count, mach_time_factor, last_time, \
            jank_count, big_jank_count, jank_time_count, _list
        if type(res.selector) is InstrumentRPCParseError:
            for args in kperf_data(res.selector.data):
                _time, code = args[0], args[7]
                if kdbg_extract_all(code) == (0x31, 0x80, 0xc6):
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

                if time_count > NANO_SECOND:
                    print(
                        {"time": datetime.now().timestamp() - last_time, "fps": frame_count / time_count * NANO_SECOND,
                         "jank": jank_count, "big_jank": big_jank_count, "stutter": jank_time_count / time_count})
                    jank_count = 0
                    big_jank_count = 0
                    jank_time_count = 0
                    frame_count = 0
                    time_count = 0

    with InstrumentsBase(udid=udid, network=network) as rpc:
        rpc.core_profile_session(on_graphics_message)


@instruments.command('notifications', cls=Command)
def cmd_notifications(udid, network, format):
    """Get mobile notifications
    """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        machTimeInfo = rpc.instruments.call(InstrumentsService.DeviceInfo.value, "machTimeInfo").selector
        mach_absolute_time = machTimeInfo[0]
        numer = machTimeInfo[1]
        denom = machTimeInfo[2]
        usecs_since_epoch = rpc.lockdown.get_value(key='TimeIntervalSince1970') * 1000000

        def on_callback_message(res):
            data = res.auxiliaries[0]
            tim = (data['mach_absolute_time'] - mach_absolute_time) * numer / denom / 1000
            data['time'] = str(datetime.fromtimestamp((usecs_since_epoch + tim) / 1000000))
            print_json(res.auxiliaries, format)

        rpc.mobile_notifications(on_callback_message)


@instruments.command('stackshot', cls=Command)
@click.option('--out', type=click.File('w'), default=None)
def stackshot(udid, network, format, out):
    """ Dump stack snapshot information. """
    with InstrumentsBase(udid=udid, network=network) as rpc:

        if rpc.lockdown.ios_version < Version('12.0'):
            log.warning('The interface requires iOS version 12+')
            return
        stopSignal = threading.Event()

        def on_callback_message(res):
            if isinstance(res.selector, InstrumentRPCParseError):
                buf = res.selector.data
                if buf.startswith(b'\x07X\xa2Y'):
                    stopSignal.set()
                    kc_data = kc_data_parse(buf)
                    if out is not None:
                        json.dump(kc_data, out, indent=4)
                        log.info(f'Successfully dump stackshot to {out.name}')
                    else:
                        print_json(kc_data, format)

        rpc.core_profile_session(on_callback_message, stopSignal)


@instruments.command('core_profile', cls=Command)
@click.option('--pid', type=click.INT, default=None, help='Process ID to filter')
@click.option('--process-name', default=None, help='Process name to filter')
def stackshot(udid, network, format, pid, process_name):
    """ Dump stack snapshot information. """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        config = {
            'tc': [{
                'csd': 128,
                'kdf2': {0xffffffff},
                'ta': [[3], [0], [2], [1, 1, 0]],
                'tk': 3,
                'uuid': str(uuid.uuid4()),
            }],
            'rp': 100,
            'bm': 0,
        }
        rpc.core_profile(config, pid, process_name)


@instruments.command('gpu_counters', cls=Command)
def gpu_counters(udid, network, format):
    """ Metal GPU Counters """
    stopSignal = threading.Event()
    signal.signal(signal.SIGINT, lambda x, y: stopSignal.set())
    with InstrumentsBase(udid=udid, network=network) as rpc:
        decode_key_list = []
        js_env: JSEvn = None
        display_key_list = []

        def dropped_message(res):
            nonlocal js_env, decode_key_list, display_key_list
            if res.selector[0] == 1:
                js_env.dump_trace(TraceData(*res.selector[:6]))
            elif res.selector[0] == 0:
                _data = res.selector[4]
                decode_key_list = GRCDecodeOrder.decode(_data.get(1))
                display_key_list = GRCDisplayOrder.decode(_data.get(0))
                js_env = JSEvn(_data.get(2), display_key_list, decode_key_list, mach_time_factor)

        machTimeInfo = rpc.device_info.machTimeInfo()
        mach_time_factor = machTimeInfo[1] / machTimeInfo[2]
        data = rpc.gpu_counters(callback=dropped_message, stopSignal=stopSignal)
        js_env.dump_trace(TraceData(*data[0][:6]))


@instruments.command('app_lifecycle', cls=Command)
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId')
def cmd_app_lifecycle(udid, network, format, bundle_id):
    with InstrumentsBase(udid=udid, network=network) as rpc:
        rpc.app_launch_lifecycle(bundle_id)

import dataclasses
import json
import threading
import uuid
from copy import deepcopy
from datetime import datetime
from distutils.version import LooseVersion

import click

from ios_device.cli.base import InstrumentsBase
from ios_device.cli.cli import Command, print_json
from ios_device.util import Log, api_util
from ios_device.util.exceptions import InstrumentRPCParseError
from ios_device.util.kc_data import kc_data_parse
from ios_device.util.utils import DumpDisk, DumpNetwork, DumpMemory
from ios_device.util.variables import LOG

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
    """ Get performance data """

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


@instruments.command('notifications', cls=Command)
def cmd_notifications(udid, network, format):
    """Get mobile notifications
    """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        def on_callback_message(res):
            print_json(res.auxiliaries, format)

        rpc.mobile_notifications(on_callback_message)


@instruments.command('stackshot', cls=Command)
@click.option('--out', type=click.File('w'), default=None)
def stackshot(udid, network, format, out):
    """ Dump stack snapshot information. """
    with InstrumentsBase(udid=udid, network=network) as rpc:

        if rpc.lock_down.ios_version < LooseVersion('12.0'):
            log.warn('The interface requires iOS version 12+')
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
@click.option('--process-name',default=None, help='Process name to filter')
def stackshot(udid, network, format,pid,process_name):
    """ Dump stack snapshot information. """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        config={
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
        rpc.core_profile(config,pid,process_name)
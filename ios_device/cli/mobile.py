import functools
import io
import sys

import click

from ios_device.cli.base import InstrumentsBase
from ios_device.cli.cli import Command, print_json
from ios_device.servers.Installation import InstallationProxyService
from ios_device.servers.crash_log import CrashLogService
from ios_device.servers.diagnostics_relay import DiagnosticsRelayService
from ios_device.servers.house_arrest import HouseArrestService
from ios_device.servers.mc_install import MCInstallService
from ios_device.servers.pcapd import PcapdService, PCAPPacketDumper
from ios_device.servers.syslog import SyslogServer
from ios_device.util import Log
from ios_device.util.lockdown import LockdownClient
from ios_device.util.usbmux import USBMux
from ios_device.util.variables import LOG

log = Log.getLogger(LOG.Mobile.value)


@click.group()
def cli():
    """ instruments cli """


@cli.group(short_help='crash report options')
def crash():
    """
    获取 crash log 相关信息
    crash report options
    """


@crash.command('delete', cls=Command)
@click.option('--name', help='crash name')
def crash_delete(udid, network, format, name):
    """ remove crash report """
    crash_server = CrashLogService(udid=udid, network=network, logger=log)
    crash_server.delete_crash(name)


@crash.command('export', cls=Command)
@click.option('--name', help='crash name')
def crash_export(udid, network, format, name):
    """ pull crash report """
    crash_server = CrashLogService(udid=udid, network=network, logger=log)
    crash_server.export_crash(name)


@crash.command('list', cls=Command)
def crash_list(udid, network, format):
    """ Show crash list """
    crash_server = CrashLogService(udid=udid, network=network, logger=log)
    crash_server.get_list()


@crash.command('shell', cls=Command)
def crash_shell(udid, network, format):
    """ Open command line mode """
    crash_server = CrashLogService(udid=udid, network=network, logger=log)
    crash_server.shell()


#######################################################################

@cli.command('sandbox', cls=Command)
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId to filter')
@click.option('-a', '--access_type', default='VendDocuments', type=click.Choice(['VendDocuments', 'VendContainer']),
              help='Type of access sandbox')
def sandbox(udid, network, format, bundle_id, access_type):
    """ open an AFC shell for given bundle_id, assuming its profile is installed """
    HouseArrestService(udid=udid, network=network, logger=log).shell(bundle_id, cmd=access_type)


#######################################################################

@cli.command('devices', cls=Command)
def cmd_devices(udid, network, format):
    """ get device list """
    print_json(USBMux().get_devices(network), format)


@cli.command('deviceinfo', cls=Command)
def cmd_deviceinfo(udid, network, format):
    """ open an AFC shell for given bundle_id, assuming its profile is installed """
    device_info = LockdownClient(udid=udid, network=network).get_value()
    print_json(device_info,format=format)


#######################################################################

@cli.group(short_help='crash report options')
def profiles():
    """
    描述文件管理 例如：安装 卸载 Fiddler 证书等

    profiles & Device Management
    """


@profiles.command('list', cls=Command)
def profile_list(udid, network, format):
    """ list installed profiles """
    print_json(MCInstallService(udid=udid, network=network, logger=log).get_profile_list(), format)


@profiles.command('install', cls=Command)
@click.option('--path', type=click.File('rb'))
def profile_install(udid, network, format, path):
    """ install given profile file """
    print_json(MCInstallService(udid=udid, network=network, logger=log).install_profile(path.read()), format)


@profiles.command('remove', cls=Command)
@click.option('--name')
def profile_remove(udid, network, format, name):
    """ remove profile by name """
    print_json(MCInstallService(udid=udid, network=network, logger=log).remove_profile(name), format)


#######################################################################

@cli.command('syslog', cls=Command)
@click.option('--path', type=click.File('wt'), help='full path to the log file')
@click.option('--filter', help='filter strings')
def cmd_syslog(udid, network, format, path, filter):
    """ file management per application bundle """
    server = SyslogServer(udid=udid, network=network, logger=log)
    server.watch(log_file=path, filter=filter)


#######################################################################


@cli.group()
def apps():
    """ application options """
    pass


@apps.command('list', cls=Command)
@click.option('-u', '--user', is_flag=True, help='include user apps')
@click.option('-s', '--system', is_flag=True, help='include system apps')
def apps_list(udid, network, format, user, system):
    """ list installed apps """
    app_types = []
    if user:
        app_types.append('User')
    if system:
        app_types.append('System')
    if not app_types:
        app_types = ['User', 'System']
    print_json(InstallationProxyService(udid=udid, network=network, logger=log).get_apps(app_types),format=format)


@apps.command('uninstall', cls=Command)
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId to filter')
def uninstall(udid, network, format, bundle_id):
    """ uninstall app by given bundle_id """
    print_json(InstallationProxyService(udid=udid, network=network, logger=log).uninstall(bundle_id))


@apps.command('install', cls=Command)
@click.argument('ipa_path', required=True,type=click.Path(exists=True))
def install(udid, network, format, ipa_path):
    """ install given .ipa """
    print_json(InstallationProxyService(udid=udid, network=network, logger=log).install(ipa_path))


@apps.command('upgrade', cls=Command)
@click.option('--ipa_path', type=click.Path(exists=True))
def upgrade(udid, network, format, ipa_path):
    """ install given .ipa """
    print_json(InstallationProxyService(udid=udid, network=network, logger=log).upgrade(ipa_path))


@apps.command('shell', cls=Command)
@click.option('-b', '--bundle_id', default=None,required=True, help='Process app bundleId to filter')
@click.option('-a', '--access_type', default='VendDocuments', type=click.Choice(['VendDocuments', 'VendContainer']),
              help='filter VendDocuments or VendContainer')
def shell(udid, network, format, bundle_id, access_type):
    """ open an AFC shell for given bundle_id, assuming its profile is installed """
    HouseArrestService(udid=udid, network=network, logger=log).shell(bundle_id, cmd=access_type)


@apps.command('launch', cls=Command)
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


@apps.command('kill', cls=Command)
@click.option('-p', '--pid', type=click.INT, default=None, help='Process ID to filter')
@click.option('-n', '--name', default=None, help='Process app name to filter')
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId to filter')
def cmd_kill(udid, network, format, pid, name, bundle_id):
    """ Kill a process by its pid. """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        if bundle_id or name:
            pid = rpc.get_pid(bundle_id, name)
        if not pid:
            log.warn(f'The {bundle_id, name, pid} did not start')
        rpc.kill_app(pid)
        print(f'Kill {pid} ...')


#######################################################################

@cli.command('pcapd', cls=Command)
@click.argument('outfile', required=True)
def cmd_pcapd(udid, network, format, outfile):
    """ sniff device traffic

    :param outfile: output file  or (- for stdout)
    """

    if outfile == '-':
        out_file = sys.stdout.buffer
        while isinstance(out_file, io.BufferedWriter):
            out_file = out_file.detach()
    else:
        out_file = open(outfile, 'wb', 0)
    num_packets = 0
    stderr_print = functools.partial(print, file=sys.stderr)

    def packet_callback(pkt):
        nonlocal num_packets
        num_packets += 1
        stderr_print('\r{} packets captured.'.format(num_packets), end='', flush=True)

    try:
        packet_extractor = PcapdService(udid=udid, network=network)
        packet_dumper = PCAPPacketDumper(packet_extractor, out_file)
        packet_dumper.run(packet_callback)
    except KeyboardInterrupt:
        stderr_print()
        stderr_print('closing capture ...')
        out_file.close()
    except:
        stderr_print()


#######################################################################

@cli.command('battery', cls=Command)
def cmd_battery(udid, network, format):
    """ get device battery
    """
    io_registry = DiagnosticsRelayService(udid=udid, network=network, logger=log).get_battery()
    print_json(io_registry, format=format)
    update_time = io_registry.get('UpdateTime')
    voltage = io_registry.get('Voltage')
    instant_amperage = io_registry.get('InstantAmperage')
    temperature = io_registry.get('Temperature')
    current = abs(instant_amperage)
    power = current * voltage / 1000
    log.info(
        f"[Battery] time={update_time}, current={current}, voltage={voltage}, power={power}, temperature={temperature}")

#
# @information.command('battery', cls=Command)
# def cmd_battery(udid, network, format):
#     """ get device battery
#     """
#     return

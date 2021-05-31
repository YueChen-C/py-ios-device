import click

from ios_device.cli.base import InstrumentsBase
from ios_device.cli.cli import Command, print_json
from ios_device.servers.Installation import InstallationProxyService
from ios_device.servers.crash_log import CrashLogService
from ios_device.servers.house_arrest import HouseArrestService
from ios_device.servers.mc_install import MCInstallService
from ios_device.servers.syslog import SyslogServer
from ios_device.util import Log
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
def crash_delete(udid, network, json_format, name):
    """ remove crash report """
    crash_server = CrashLogService(udid=udid, network=network, logger=log)
    crash_server.delete_crash(name)


@crash.command('export', cls=Command)
@click.option('--name', help='crash name')
def crash_export(udid, network, json_format, name):
    """ pull crash report """
    crash_server = CrashLogService(udid=udid, network=network, logger=log)
    crash_server.export_crash(name)


@crash.command('list', cls=Command)
def crash_list(udid, network, json_format):
    """ Show crash list """
    crash_server = CrashLogService(udid=udid, network=network, logger=log)
    crash_server.get_list()


@crash.command('shell', cls=Command)
def crash_shell(udid, network, json_format):
    """ Open command line mode """
    crash_server = CrashLogService(udid=udid, network=network, logger=log)
    crash_server.shell()


@cli.command('house', cls=Command)
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId to filter')
def cmd_house(udid, network, json_format, bundle_id):
    """ file management per application bundle """
    crash_server = HouseArrestService(udid=udid, network=network, logger=log)
    crash_server.shell(bundle_id)


#######################################################################

@cli.group(short_help='crash report options')
def profiles():
    """
    描述文件管理 例如：安装 卸载 Fiddler 证书等

    profiles & Device Management
    """


@profiles.command('list', cls=Command)
def profile_list(udid, network, json_format):
    """ list installed profiles """
    print_json(MCInstallService(udid=udid, network=network, logger=log).get_profile_list(), json_format)


@profiles.command('install', cls=Command)
@click.option('--path', type=click.File('rb'))
def profile_install(udid, network, json_format, path):
    """ install given profile file """
    print_json(MCInstallService(udid=udid, network=network, logger=log).install_profile(path.read()), json_format)


@profiles.command('remove', cls=Command)
@click.option('--name')
def profile_remove(udid, network, json_format, name):
    """ remove profile by name """
    print_json(MCInstallService(udid=udid, network=network, logger=log).remove_profile(name), json_format)


#######################################################################

@cli.command('syslog', cls=Command)
@click.option('--path', type=click.File('wt'), help='full path to the log file')
@click.option('--filter', help='filter strings')
def cmd_syslog(udid, network, json_format, path, filter):
    """ file management per application bundle """
    server = SyslogServer(udid=udid, network=network, logger=log)
    server.watch(log_file=path, filter=filter)


#######################################################################


@click.group()
def cli():
    """ apps cli """
    pass


@cli.group()
def apps():
    """ application options """
    pass


@apps.command('list', cls=Command)
@click.option('-u', '--user', is_flag=True, help='include user apps')
@click.option('-s', '--system', is_flag=True, help='include system apps')
def apps_list(udid, network, json_format, user, system):
    """ list installed apps """
    app_types = []
    if user:
        app_types.append('User')
    if system:
        app_types.append('System')
    if not app_types:
        app_types = ['User', 'System']
    print_json(InstallationProxyService(udid=udid, network=network, logger=log).get_apps(app_types))


@apps.command('uninstall', cls=Command)
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId to filter')
def uninstall(udid, network, json_format, bundle_id):
    """ uninstall app by given bundle_id """
    print_json(InstallationProxyService(udid=udid, network=network, logger=log).uninstall(bundle_id))


@apps.command('install', cls=Command)
@click.option('--ipa_path', type=click.Path(exists=True))
def install(udid, network, json_format, ipa_path):
    """ install given .ipa """
    print_json(InstallationProxyService(udid=udid, network=network, logger=log).install(ipa_path))


@apps.command('upgrade', cls=Command)
@click.option('--ipa_path', type=click.Path(exists=True))
def upgrade(udid, network, json_format, ipa_path):
    """ install given .ipa """
    print_json(InstallationProxyService(udid=udid, network=network, logger=log).upgrade(ipa_path))


@apps.command('shell', cls=Command)
@click.option('-b', '--bundle_id', default=None, help='Process app bundleId to filter')
def shell(udid, network, json_format, bundle_id):
    """ open an AFC shell for given bundle_id, assuming its profile is installed """
    HouseArrestService(udid=udid, network=network, logger=log).shell(bundle_id)


@apps.command('launch', cls=Command)
@click.option('--bundle_id', default=None, help='Process app bundleId to filter')
@click.option('--app_env', default=None, help='App launch environment variable')
def cmd_launch(udid, network, json_format, bundle_id: str, app_env: dict):
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
def cmd_kill(udid, network, json_format, pid, name, bundle_id):
    """ Kill a process by its pid. """
    with InstrumentsBase(udid=udid, network=network) as rpc:
        if bundle_id or name:
            pid = rpc.get_pid(bundle_id, name)
        if not pid:
            log.warn(f'The {bundle_id, name, pid} did not start')
        rpc.kill_app(pid)
        print(f'Kill {pid} ...')


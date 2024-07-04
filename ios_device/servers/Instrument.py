from packaging.version import Version

from ..remote.remote_lockdown import RemoteLockdownClient
from ..servers.dvt import DTXServer
from ..util import Log
from ios_device.util.lockdown import LockdownClient
from ..util.variables import LOG

log = Log.getLogger(LOG.Instrument.value)


class InstrumentServer(DTXServer):
    SERVICE_NAME = 'com.apple.instruments.remoteserver.DVTSecureSocketProxy'
    OLD_SERVICE_NAME = 'com.apple.instruments.remoteserver'
    RSD_SERVICE_NAME = 'com.apple.instruments.dtservicehub'

    def __init__(self, lockdown=None, udid=None, network=None):
        super().__init__()
        self.lockdown = lockdown or LockdownClient(udid=udid, network=network)

    def init(self, cli=None):
        if not cli:
            if isinstance(self.lockdown, RemoteLockdownClient):
                cli = self.lockdown.start_lockdown_developer_service(self.RSD_SERVICE_NAME)
            else:
                if self.lockdown.ios_version >= Version('14.0'):
                    cli = self.lockdown.start_service(self.SERVICE_NAME)
                else:
                    cli = self.lockdown.start_service(self.OLD_SERVICE_NAME)
                    if hasattr(cli.sock, '_sslobj'):
                        cli.sock._sslobj = None  # remoteserver 协议配对成功之后，需要关闭 ssl 协议通道，使用明文传输
        return super().init(cli)

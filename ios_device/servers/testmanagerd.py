from distutils.version import LooseVersion

from ..servers.dvt import DTXServer
from ..util.exceptions import StartServiceError
from ..util.lockdown import LockdownClient


class TestManagerdLockdown(DTXServer):
    def __init__(self, lockdown=None, udid=None, *args, **kw):
        super().__init__(*args, **kw)
        self.lockdown = lockdown or LockdownClient(udid=udid)

    def init(self, cli=None):
        if not cli:
            if self.lockdown.ios_version >= LooseVersion('14.0'):
                cli = self.lockdown.start_service("com.apple.testmanagerd.lockdown.secure")
            else:
                cli = self.lockdown.start_service("com.apple.testmanagerd.lockdown")
                if hasattr(cli.sock, '_sslobj'):
                    cli.sock._sslobj = None  # remoteserver 协议配对成功之后，需要关闭 ssl 协议通道，使用明文传输
        return super().init(cli)

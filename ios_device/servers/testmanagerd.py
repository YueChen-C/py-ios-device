from distutils.version import LooseVersion

from ..servers.dvt import DTXServer
from ..util.exceptions import StartServiceError
from ..util.lockdown import LockdownClient


class TestManagerdLockdown(DTXServer):
    def __init__(self, lockdown=None,udid=None,*args, **kw):
        super().__init__(*args, **kw)
        self.lockdown = lockdown if lockdown else LockdownClient(udid=udid)

    def init(self,_cli=None):
        """
        初始化 servers rpc 服务:
        :return: bool 是否成功
        """
        try:
            if self.lockdown.ios_version >= LooseVersion('14.0'):
                self._cli = self.lockdown.start_service("com.apple.testmanagerd.lockdown.secure")
            else:
                self._cli = self.lockdown.start_service("com.apple.testmanagerd.lockdown")
                if hasattr(self._cli.sock, '_sslobj'):
                    self._cli.sock._sslobj = None  # remoteserver 协议配对成功之后，需要关闭 ssl 协议通道，使用明文传输
        except StartServiceError as E:
            raise E
        if self._cli is None:
            return False
        self._start()
        return self

from distutils.version import LooseVersion

from ..servers.DTXSever import DTXServerRPC
from ..util.exceptions import StartServiceError


class InstrumentServer(DTXServerRPC):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    def init(self):
        """
        初始化 servers rpc 服务:
        :return: bool 是否成功
        """
        try:
            if self.lockdown.ios_version >= LooseVersion('14.0'):
                self._cli = self.lockdown.start_service("com.apple.instruments.remoteserver.DVTSecureSocketProxy")
            else:
                self._cli = self.lockdown.start_service("com.apple.instruments.remoteserver")
                if hasattr(self._cli.sock, '_sslobj'):
                    self._cli.sock._sslobj = None  # remoteserver 协议配对成功之后，需要关闭 ssl 协议通道，使用明文传输
        except StartServiceError as E:
            raise E
        self._start()
        if self._cli is None:
            return False
        return self

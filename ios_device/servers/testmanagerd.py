from distutils.version import LooseVersion

from ..servers.DTXSever import DTXServerRPC, log
from ..util.exceptions import StartServiceError


class TestManagerdLockdown(DTXServerRPC):

    def init(self):
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

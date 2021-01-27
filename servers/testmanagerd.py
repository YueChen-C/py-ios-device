from servers.DTXSever import DTXServerRPC, log
from util.exceptions import StartServiceError


class TestManagerdLockdown(DTXServerRPC):

    def init(self):
        """
        初始化 servers rpc 服务:
        :return: bool 是否成功
        """
        try:
            self._cli = self.lockdown.start_service("com.apple.testmanagerd.lockdown")
            if hasattr(self._cli.sock, '_sslobj'):
                self._cli.sock._sslobj = None  # remoteserver 协议配对成功之后，需要关闭 ssl 协议通道，使用明文传输
        except StartServiceError as E:
            self._cli = self.lockdown.start_service("com.apple.testmanagerd.lockdown.secure")
        if self._cli is None:
            return False
        return self

from distutils.version import LooseVersion

from ..servers.dvt import DTXServer
from ..util import Log
from ..util.exceptions import StartServiceError
from ..util.lockdown import LockdownClient
from ..util.variables import LOG

log = Log.getLogger(LOG.Instrument.value)


class InstrumentServer(DTXServer):
    def __init__(self, lockdown=None, udid=None, network=None, *args, **kw):
        super().__init__(*args, **kw)
        self.lockdown = lockdown or LockdownClient(udid=udid, network=network)

    def init(self, _cli=None):
        """
        初始化 servers rpc 服务:
        :return: bool 是否成功
        """
        log.info('InstrumentServer init ...')
        if not _cli:
            try:
                if self.lockdown.ios_version >= LooseVersion('14.0'):
                    self._cli = self.lockdown.start_service("com.apple.instruments.remoteserver.DVTSecureSocketProxy")
                else:
                    self._cli = self.lockdown.start_service("com.apple.instruments.remoteserver")
                    if hasattr(self._cli.sock, '_sslobj'):
                        self._cli.sock._sslobj = None  # remoteserver 协议配对成功之后，需要关闭 ssl 协议通道，使用明文传输
            except StartServiceError as E:
                raise E
        else:
            self._cli = _cli
        self._start()
        if self._cli is None:
            return False
        return self



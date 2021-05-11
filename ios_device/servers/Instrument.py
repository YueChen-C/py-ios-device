import logging
import time
import uuid
from distutils.version import LooseVersion

from ..servers.DTXSever import DTXServerRPC
from ..util import Log
from ..util.exceptions import StartServiceError
from ..util.lockdown import LockdownClient
from ..util.utils import wait_for_wireless
from ..util.variables import LOG

log = Log.getLogger(LOG.Instrument.value)


class InstrumentServer(DTXServerRPC):
    def __init__(self, lockdown=None, udid=None, network=None, *args, **kw):
        super().__init__(*args, **kw)
        self.lockdown = lockdown if lockdown else LockdownClient(udid=udid, network=network)

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

    def start_wireless(self):
        """ 启用 wifi 连接模式
        :return:
        """
        if not self._cli:
            self.init()

        def dropped_message(res):
            print("[DROP]", res.plist, res.raw.channel_code)

        def channel_canceled(res):
            print("not supported:", res.plist)
            self.stop()

        self.register_unhandled_callback(dropped_message)
        self.register_callback("_channelCanceled:", channel_canceled)
        channel = "com.apple.instruments.server.services.wireless"
        while 1:
            enabled = self.call(channel, "isServiceEnabled").parsed
            if not enabled:
                break
            ## 可以不清理删除，但必须使用上次 startServerDaemonWithName 值来进行操作，可以把 startServerDaemonWithName 作为变量保存
            print("remove", self.call(channel, "removeDaemonFromService").parsed)
            time.sleep(1)
        psk = uuid.uuid4().hex  ## 加解密秘钥
        name = self.lockdown.udid[-4:]  ## 协议名字
        service_name = self.lockdown.udid[-8:]  ##协议头，类似http,tcp 等_1993b8d3._tcp.local.
        print("start",
              self.call(channel, "startServerDaemonWithName:type:passphrase:", "perfcat_" + name, service_name,
                        psk).parsed)
        enabled = self.call(channel, "isServiceEnabled").parsed
        print("enabled", enabled)
        self.stop()
        if not enabled:
            raise Exception('start wireless error')
        addresses, port = wait_for_wireless(name, service_name)

        return addresses, port, psk

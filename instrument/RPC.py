import time
import time
import traceback
from ctypes import sizeof
from threading import Thread, Event

from instrument.bpylist import archiver
from instrument.bpylist.bplistlib.readwrite import load
from instrument.dtxlib import DTXMessage, DTXMessageHeader, \
    pyobject_to_auxiliary, \
    pyobject_to_selector, selector_to_pyobject
from util import logging
from util.exceptions import StartServiceError
from util.lockdown import LockdownClient

log = logging.getLogger(__name__)


def get_usb_rpc(udid=None):
    rpc = InstrumentRPC(udid)
    if not rpc.init(DTXUSBTransport):
        return None
    return rpc


class DTXFragment:

    def __init__(self, buf):
        self._header = DTXMessageHeader.from_buffer_copy(buf[:sizeof(DTXMessageHeader)])
        self._bufs = [buf]
        self.current_fragment_id = 0 if self._header.fragmentId == 0 else -1

    def append(self, buf):
        assert self.current_fragment_id >= 0, "attempt to append to an broken fragment"
        assert len(buf) >= sizeof(DTXMessageHeader)
        subheader = DTXMessageHeader.from_buffer_copy(buf[:sizeof(DTXMessageHeader)])
        assert subheader.fragmentCount == self._header.fragmentCount
        assert subheader.fragmentId == self.current_fragment_id + 1
        self.current_fragment_id = self.current_fragment_id + 1
        self._bufs.append(buf)

    @property
    def message(self):
        assert self.completed, "should only be called when completed"
        return DTXMessage.from_bytes(b''.join(self._bufs))

    @property
    def completed(self):
        return self.current_fragment_id + 1 == self._header.fragmentCount

    @property
    def key(self):
        return self._header.channelCode, self._header.identifier

    @property
    def header(self):
        return self._header.fragmentId == 0


class DTXClientMixin:

    def send_dtx(self, client, dtx):
        buffer = dtx.to_bytes()
        log.debug(f'发送 DTX: {buffer}')
        return self.send_all(client, buffer)

    def recv_dtx_fragment(self, client, timeout=-1):
        header_buffer = self.recv_all(client, sizeof(DTXMessageHeader), timeout=timeout)
        if not header_buffer:
            return None
        header = DTXMessageHeader.from_buffer_copy(header_buffer)
        if header.fragmentCount > 1 and header.fragmentId == 0:
            return header_buffer
        body_buffer = self.recv_all(client, header.length, timeout=timeout)
        if not body_buffer:
            return None
        return header_buffer + body_buffer

    def recv_dtx(self, client, timeout=-1):
        self._setup_manager()
        while 1:
            buf = self.recv_dtx_fragment(client, timeout)
            if not buf:
                return None
            log.debug(f'接收 DTX: {buf}')
            fragment = DTXFragment(buf)
            if fragment.completed:
                return fragment.message
            value = getattr(client, 'value', id(client))
            key = (value, fragment.key)
            if fragment.header:
                self._dtx_demux_manager[key] = fragment
            else:
                assert key in self._dtx_demux_manager
                self._dtx_demux_manager[key].append(buf)
                if self._dtx_demux_manager[key].completed:
                    ret = self._dtx_demux_manager[key].message
                    self._dtx_demux_manager.pop(key)
                    print(ret)
                    return ret

    def _setup_manager(self):
        if hasattr(self, "_dtx_demux_manager"):
            return
        self._dtx_demux_manager = {}


class DTXUSBTransport:
    """
    Instruments 服务，用于监控设备状态, 采集性能数据
    """

    def send_all(self, client, buffer: bytes) -> bool:
        """
        向 instrument client 发送整块buffer
        成功时表示整块数据都被发出
        :param client: instrument client(C对象）
        :param buffer: 数据
        :return: bool 是否成功
        """
        client.sock.send(buffer)
        return True

    def recv_all(self, client, length, timeout=-1) -> bytes:
        """
        从 instrument client 接收长度为 length 的 buffer
        成功时表示整块数据都被接收
        :param timeout:
        :param client: instrument client(C对象）
        :param length: 数据长度
        :return: 长度为 length 的 buffer, 失败时返回 None
        """
        ret = b''
        while len(ret) < length:
            L = length - len(ret)
            if L > 8192:
                L = 8192
            rb = client.recv(L, timeout)
            if not rb:
                return ret
            ret += rb
        return ret

    def pre_start(self, rpc):
        pass

    def post_start(self, rpc):
        pass


class InstrumentRPCParseError:
    pass


InstrumentServiceConnectionLost = DTXMessage().set_selector(pyobject_to_selector("[PerfCat] Connection Lost!"))


class InstrumentRPCRawArg:
    def __init__(self, data: bytes):
        self.data = data


class InstrumentRPCResult:
    def __init__(self, dtx):
        self.raw = dtx
        if self.raw is None:
            self.xml = None
            self.parsed = None
            self.plist = None
            return
        sel = dtx.get_selector()
        if not sel:
            self.xml = ""
            self.plist = ""
            self.parsed = None
            return
        try:
            self.plist = load(sel)
        except:
            self.plist = InstrumentRPCParseError()
        try:
            self.parsed = archiver.unarchive(sel)
        except:
            self.parsed = InstrumentRPCParseError()


class InstrumentRPC:

    def __init__(self, udid=None):
        self._cli = None
        self._is = None
        self._recv_thread = None
        self._running = False
        self._callbacks = {}
        self._sync_waits = {}
        self._next_identifier = 1
        self._channels = {}
        self._receiver_exiting = False
        self._unhanled_callback = None
        self._channel_callbacks = {}
        self.udid = udid
        self.lockdown = None

    def init(self, transport):
        """
        初始化 instrument rpc 服务:
        :return: bool 是否成功
        """

        class T(transport, DTXClientMixin):
            pass

        self.lockdown = self.lockdown if self.lockdown else LockdownClient(udid=self.udid)
        try:
            self._cli = self.lockdown.start_service("com.apple.instruments.remoteserver")
            if hasattr(self._cli.sock,'_sslobj'):
                self._cli.sock._sslobj = None  # remoteserver 协议配对成功之后，需要关闭 ssl 协议通道，使用明文传输
        except StartServiceError as E:
            log.debug(E)
            self._cli = self.lockdown.start_service("com.apple.instruments.remoteserver.DVTSecureSocketProxy")

        self._is = T()
        if self._cli is None:
            return False
        return True

    def deinit(self):
        """
        反初始化 instrument rpc 服务
        :return: 无返回值
        """
        if self._cli:
            self._cli.close()
            self._cli = None

    def start(self):
        """
        启动 instrument rpc 服务
        :return: bool 是否成功
        """
        if self._running:
            return True
        self._running = True
        self._recv_thread = Thread(target=self._receiver, name="InstrumentRecevier")
        self._is.pre_start(self)
        self._recv_thread.start()
        self._is.post_start(self)
        return True

    def stop(self):
        """
        停止 instrument rpc 服务
        :return: 无返回值
        """
        self._running = False
        if self._recv_thread:
            self._recv_thread.join()
            self._recv_thread = None
        pass

    def register_callback(self, selector, callback):
        """
        注册回调, 接受 instrument server 到 client 的远程调用
        :parma selector: 字符串, selector 名称
        :param callback: 回调函数, 接受一个参数, 类型是 InstrumentRPCResult 对象实例
        :return: 无返回值
        """
        self._callbacks[selector] = callback

    def register_channel_callback(self, channel, callback):
        """
        注册回调, 接受 instrument server 到 client 的远程调用
        :parma channel: 字符串, channel 名称
        :param callback: 回调函数, 接受一个参数, 类型是 InstrumentRPCResult 对象实例
        :return: 无返回值
        """
        channel_id = self._make_channel(channel)
        self._channel_callbacks[channel_id] = callback

    def register_unhandled_callback(self, callback):
        """
        注册回调, 接受 instrument server 到 client 的远程调用, 处理所以未被处理的消息
        :param callback: 回调函数, 接受一个参数, 类型是 InstrumentRPCResult 对象实例
        :return: 无返回值
        """
        self._unhanled_callback = callback

    def _make_channel(self, channel: str):
        if channel is None:
            return 0
        if channel in self._channels:
            return self._channels[channel]

        channel_id = len(self._channels) + 1
        dtx = self._call(True, 0, "_requestChannelWithCode:identifier:", channel_id, channel)
        if dtx.get_selector():
            print("Make Channel Error:", load(dtx.get_selector()))
            raise RuntimeError("failed to make channel")
        self._channels[channel] = channel_id
        return channel_id

    def call(self, channel: str, selector: str, *auxiliaries):
        channel_id = self._make_channel(channel)
        ret = self._call(True, channel_id, selector, *auxiliaries)
        log.debug(f"plist: {ret}")
        return InstrumentRPCResult(ret)

    def call_noret(self, channel: str, selector: str, *auxiliaries):
        channel_id = self._make_channel(channel)
        self._call(False, channel_id, selector, *auxiliaries)

    def _call(self, sync: bool, channel_id: int, selector: str, *auxiliaries):
        """
        :param sync: 是否回调
        :param channel_id: 通道标识
        :param selector: 请求方法名称，method name
        :param auxiliaries:
        :return:
        """
        if self._receiver_exiting:
            raise RuntimeWarning("rpc service died")
        dtx = DTXMessage()
        dtx.identifier = self._next_identifier
        self._next_identifier += 1
        dtx.channel_code = channel_id
        dtx.set_selector(pyobject_to_selector(selector))
        wait_key = (dtx.channel_code, dtx.identifier)
        for aux in auxiliaries:
            if type(aux) is InstrumentRPCRawArg:
                dtx.add_auxiliary(aux.data)
            else:
                dtx.add_auxiliary(pyobject_to_auxiliary(aux))
        if sync:
            dtx.expects_reply = True
            param = {"result": None, "event": Event()}
            self._sync_waits[wait_key] = param
        self._is.send_dtx(self._cli, dtx)
        if sync:
            param['event'].wait()
            ret = param['result']
            self._sync_waits.pop(wait_key)
            return ret

    def _receiver(self):
        last_none = 0
        while self._running:
            dtx = self._is.recv_dtx(self._cli, 2)  # s
            if dtx is None:  # 长时间没有回调则抛出错误
                cur = time.time()
                if cur - last_none < 0.1:
                    break
                last_none = cur
                continue
            self._next_identifier = max(self._next_identifier, dtx.identifier + 1)
            wait_key = (dtx.channel_code, dtx.identifier)
            if wait_key in self._sync_waits:
                param = self._sync_waits[wait_key]
                param['result'] = dtx
                param['event'].set()
            elif 2 ** 32 - dtx.channel_code in self._channel_callbacks:
                try:
                    self._channel_callbacks[2 ** 32 - dtx.channel_code](InstrumentRPCResult(dtx))
                except:
                    traceback.print_exc()
            else:
                try:
                    selector = selector_to_pyobject(dtx.get_selector())
                except:
                    selector = None

                if selector and type(selector) is str and selector in self._callbacks:
                    try:
                        ret = self._callbacks[selector](InstrumentRPCResult(dtx))
                        if dtx.expects_reply:
                            reply = dtx.new_reply()
                            reply.set_selector(pyobject_to_selector(ret))
                            reply._payload_header.flags = 0x3
                            self._is.send_dtx(self._cli, reply)
                    except:
                        traceback.print_exc()
                else:
                    if self._unhanled_callback:
                        try:
                            self._unhanled_callback(InstrumentRPCResult(dtx))
                        except:
                            traceback.print_exc()
        self._receiver_exiting = True  # to block incoming calls
        for wait_key in self._sync_waits:
            self._sync_waits[wait_key]['result'] = InstrumentServiceConnectionLost
            self._sync_waits[wait_key]['event'].set()


def pre_call(rpc):
    done = Event()

    def _notifyOfPublishedCapabilities(res):
        done.set()

    def dropped_message(res):
        print("[DROP]", res.parsed, res.raw.channel_code)

    rpc.register_callback("_notifyOfPublishedCapabilities:", _notifyOfPublishedCapabilities)
    rpc.register_unhandled_callback(dropped_message)
    rpc.start()
    if not done.wait(5):
        print("[WARN] timeout waiting capabilities")


if __name__ == '__main__':

    buf=bytes.fromhex('795b3d1f2000000000000100080400008d000000000000001f000000010000000200000053030000f803000000000000f00100000000000043030000000000000a000000020000003a02000062706c6973743030d40102030405062d2e582476657273696f6e58246f626a65637473592461726368697665725424746f7012000186a0af101007081a1b1c1d1e1f202122232425262755246e756c6cd2090a0b195a4e532e6f626a656374735624636c617373ad0c0d0e0f10111213141516171880028003800480058006800780088009800a800b800c800d800e800f5f10126e65742e72782e62797465732e64656c74615f10146e65742e74782e7061636b6574732e64656c74615c6e65742e74782e62797465735f10146e65742e72782e7061636b6574732e64656c74615b6e65742e7061636b6574735f10126e65742e74782e62797465732e64656c74615e6e65742e74782e7061636b6574735c6e65742e72782e62797465735f100f6e65742e62797465732e64656c74615f10116e65742e7061636b6574732e64656c74615e6e65742e72782e7061636b6574735f10116e65742e636f6e6e656374696f6e735b5d596e65742e6279746573d228292a2b5a24636c6173736e616d655824636c6173736573554e53536574a22a2c584e534f626a6563745f100f4e534b657965644172636869766572d12f3054726f6f74800100080011001a0023002d00320037004a0050005500600067007500770079007b007d007f00810083008500870089008b008d008f009100a600bd00ca00e100ed01020111011e0130014401530167017101760181018a01900193019c01ae01b101b600000000000002010000000000000031000000000000000000000000000001b80a00000002000000f100000062706c6973743030d4010203040515161758246f626a65637473582476657273696f6e592461726368697665725424746f70a406070d0e55246e756c6cd208090a0b5624636c6173735a4e532e6f626a656374738003a10c800211a052d20f1011125a24636c6173736e616d655824636c61737365735c4e534d757461626c65536574a3111314554e53536574584e534f626a65637412000186a05f100f4e534b657965644172636869766572d1181954726f6f74800108111a232d32373d42495456585a5d626d7683878d969badb0b50000000000000101000000000000001a000000000000000000000000000000b762706c6973743030d4010203040506070a582476657273696f6e592461726368697665725424746f7058246f626a6563747312000186a05f100f4e534b657965644172636869766572d1080954726f6f748001a20b0c55246e756c6c5f101973616d706c65417474726962757465733a666f72504944733a08111a24293237494c5153565c0000000000000101000000000000000d00000000000000000000000000000078795b3d1f2000000000000100620300008c00000000000000200000000100000002000000ad0200005203000000000000f0010000000000009d020000000000000a000000020000009401000062706c6973743030d40102030405062122582476657273696f6e58246f626a65637473592461726368697665725424746f7012000186a0aa07081415161718191a1b55246e756c6cd2090a0b135a4e532e6f626a656374735624636c617373a70c0d0e0f101112800280038004800580068007800880095b656e657267792e636f73745a656e657267792e4350555f1011656e657267792e6e6574776f726b696e675f100f656e657267792e6c6f636174696f6e5a656e657267792e4750555f100f656e657267792e61707073746174655f100f656e657267792e6f76657268656164d21c1d1e1f5a24636c6173736e616d655824636c6173736573554e53536574a21e20584e534f626a6563745f100f4e534b657965644172636869766572d1232454726f6f74800100080011001a0023002d0032003700420048004d0058005f00670069006b006d006f00710073007500770083008e00a200b400bf00d100e300e800f300fc01020105010e012001230128000000000000020100000000000000250000000000000000000000000000012a0a00000002000000f100000062706c6973743030d4010203040515161758246f626a65637473582476657273696f6e592461726368697665725424746f70a406070d0e55246e756c6cd208090a0b5624636c6173735a4e532e6f626a656374738003a10c800211a052d20f1011125a24636c6173736e616d655824636c61737365735c4e534d757461626c65536574a3111314554e53536574584e534f626a65637412000186a05f100f4e534b657965644172636869766572d1181954726f6f74800108111a232d32373d42495456585a5d626d7683878d969badb0b50000000000000101000000000000001a000000000000000000000000000000b762706c6973743030d4010203040506070a582476657273696f6e592461726368697665725424746f7058246f626a6563747312000186a05f100f4e534b657965644172636869766572d1080954726f6f748001a20b0c55246e756c6c5f101973616d706c65417474726962757465733a666f72504944733a08111a24293237494c5153565c0000000000000101000000000000000d00000000000000000000000000000078')
    # buf1 = b'y[=\x1f \x00\x00\x00\x00\x00\x01\x00\xcd\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x02\x00\x00\x00\x1c\x00\x00\x00\xbd\x00\x00\x00\x00\x00\x00\x00\xf0\x01\x00\x00\x00\x00\x00\x00\x0c\x00\x00\x00\x00\x00\x00\x00\n\x00\x00\x00\x03\x00\x00\x00)/\x00\x00bplist00\xd4\x01\x02\x03\x04\x05\x06\x07\nY$archiverX$versionX$objectsT$top_\x10\x0fNSKeyedArchiver\x12\x00\x01\x86\xa0\xa2\x08\tU$null_\x10\x15startSamplingWithPid:\xd1\x0b\x0cTroot\x80\x01\x08\x11\x1b$-2DILRjmr\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00t'
    dtx = DTXFragment(buf)

    print(dtx.message)

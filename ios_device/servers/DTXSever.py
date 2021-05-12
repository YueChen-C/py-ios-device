import enum
import plistlib
import socket
import struct
import threading
import time
import traceback
import typing
from ctypes import sizeof
from threading import Thread, Event

from ..util import logging, Log
from ..util.bpylist2 import unarchive
from ..util.dtxlib import DTXMessage, DTXMessageHeader, \
    pyobject_to_auxiliary, get_auxiliary_text, \
    pyobject_to_selector, selector_to_pyobject, ns_keyed_archiver, auxiliary_to_pyobject
from ..util.plist_service import PlistService
from ..util.ca import AESCrypto
from ..util.variables import LOG

log = Log.getLogger(LOG.Instrument.value)


class DTXEnum(str, enum.Enum):
    NOTIFICATION = "notification:"
    FINISHED = "finished:"
    OTHER = "other:"


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


class DTXUSBTransport:
    """
    Instruments 服务，用于监控设备状态, 采集性能数据
    """

    def send_all(self, client, buffer: bytes) -> bool:
        """
        向 servers client 发送整块buffer
        成功时表示整块数据都被发出
        :param client: servers client(C对象）
        :param buffer: 数据
        :return: bool 是否成功
        """

        client.send(buffer)
        return True

    def recv_all(self, client, length, timeout=-1) -> bytes:
        """
        从 servers client 接收长度为 length 的 buffer
        成功时表示整块数据都被接收
        :param timeout:
        :param client: servers client(C对象）
        :param length: 数据长度
        :return: 长度为 length 的 buffer, 失败时返回 None
        """
        ret = b''
        rb = None
        while len(ret) < length:
            L = length - len(ret)
            if L > 8192:
                L = 8192
            if isinstance(client, PlistService):
                rb = client.recv(L)
            else:
                try:
                    client.settimeout(1)  # 毫秒, 需要转成秒
                    rb = client.recv(L)
                    client.settimeout(None)
                except socket.timeout:
                    pass
            if not rb:
                return ret
            ret += rb
        return ret


class DTXClientMixin(DTXUSBTransport):

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
            log.debug(f'接收 DTX: {buf}')
            if not buf:
                return None
            fragment = DTXFragment(buf)
            if fragment.completed:
                message = fragment.message
                try:
                    log.debug(f'接收 DTX Data: {selector_to_pyobject(message._selector)} :{get_auxiliary_text(message)}')
                    if '_channelCanceled:' in selector_to_pyobject(message._selector):
                        client.close()
                except Exception as e:
                    log.debug(f'Decode DTX error: {message._buf}')
                return message
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
                    return ret

    def _setup_manager(self):
        if hasattr(self, "_dtx_demux_manager"):
            return
        self._dtx_demux_manager = {}


class InstrumentRPCParseError:
    pass


InstrumentServiceConnectionLost = DTXMessage().set_selector(pyobject_to_selector("[PerfCat] Connection Lost!"))


class DTXServerRPCRawArg:
    def __init__(self, data: bytes):
        self.data = data


class DTXServerRPCRawObj:
    def __init__(self, *data):
        self.data = data

    def to_bytes(self):
        _bytes = b''
        for val in self.data:
            buf = ns_keyed_archiver(val)
            _bytes += struct.pack('<iii', 0xa, 2, len(buf)) + buf
        return _bytes


class DTXServerRPCResult:

    def __init__(self, dtx):
        self.raw = dtx
        self.parsed = None
        self.plist = None
        self.auxiliary = None
        if dtx:
            sel = dtx.get_selector()
            if not sel:
                return
            self.auxiliary = get_auxiliary_text(dtx)
            try:
                self.plist = plistlib.loads(sel)
            except:
                self.plist = InstrumentRPCParseError()
            try:
                self.parsed = unarchive(sel)
            except:

                self.parsed = InstrumentRPCParseError()


class DTXServerRPC:

    def __init__(self, lockdown=None, udid=None):
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
        self._published_capabilities = None
        self._channel_callbacks = {}
        self.udid = udid
        self.lockdown = lockdown
        self._is = DTXClientMixin()

        self.done = Event()
        self.register()

    def register(self):
        def _notifyOfPublishedCapabilities(res):
            self.done.set()
            self._published_capabilities = get_auxiliary_text(res.raw)

        self.register_callback("_notifyOfPublishedCapabilities:", _notifyOfPublishedCapabilities)

    def init(self, _cli=None):
        """ 继承类
        初始化 servers rpc 服务:
        :return: bool 是否成功
        """
        self._cli = _cli
        self._start()
        return self

    @classmethod
    def init_wireless(self, addresses, port, psk):
        _cli = None
        try:
            for address in addresses:
                _cli = socket.create_connection((address, int(port)), timeout=3)
                break
        except Exception:
            pass
        logging.info(f'等待连接 IP 地址回调数据: {addresses}:{port}')
        if not _cli:
            raise Exception(f'wifi连接失败: addresses:{addresses},port:{port} ')
        DTXServer = DTXServerRPC()
        _done = threading.Event()

        def challenge(res):
            val = auxiliary_to_pyobject(res.raw.get_auxiliary_at(0))
            val = bytes(val)
            d_val = AESCrypto.cbc_decrypt(val, bytes(psk, encoding='utf8'))
            out = AESCrypto.cbc_encrypt(d_val[:-1] + b'ack\x00', bytes(psk, encoding='utf8'))
            _done.set()
            return out

        DTXServer.register_callback("challenge:", challenge)
        DTXServer.init(_cli)
        while not _done.wait(5):
            logging.debug("[WIRELESS] challange callback registered error")
            return False

        print("[WIRELESS] challange callback registered")
        return DTXServer

    def _start(self):
        """
        启动 servers rpc 服务, 此接口用户无需调用, 用户使用 init 接口
        :return: bool 是否成功
        """
        if self._running:
            return True
        self._running = True
        self._recv_thread = Thread(target=self._receiver, name="InstrumentRecevier")
        self._recv_thread.start()
        while not self.done.wait(5):
            logging.debug("[WARN] timeout waiting capabilities")
            return False
        return True

    def stop(self):
        """
        停止 servers rpc 服务
        :return: 无返回值
        """
        self._running = False
        if self._recv_thread:
            self._recv_thread = None
        if self._cli:
            self._cli.close()
            self._cli = None
        if self._sync_waits:
            for key, param in self._sync_waits.items():
                if param.get('event'):
                    param.get('event').set()

    def _run_callbacks(self, event_name, data):
        """
        Returns:
            if called
        """
        func = self._callbacks.get(event_name)
        if func:
            func(data)
            return True

    def register_callback(self, selector, callback: typing.Callable):
        """
        注册回调, 接受 servers server 到 client 的远程调用
        :parma selector: 字符串, selector 名称
        :param callback: 回调函数, 接受一个参数, 类型是 InstrumentRPCResult 对象实例
        :return: 无返回值
        """
        self._callbacks[selector] = callback

    def register_channel_callback(self, channel, callback):
        """
        注册回调, 接受 servers server 到 client 的远程调用
        :parma channel: 字符串, channel 名称
        :param callback: 回调函数, 接受一个参数, 类型是 InstrumentRPCResult 对象实例
        :return: 无返回值
        """
        log.info(f'set {channel} callback ...')
        channel_id = self._make_channel(channel)
        self._channel_callbacks[channel_id] = callback

    def register_unhandled_callback(self, callback):
        """
        注册回调, 接受 servers server 到 client 的远程调用, 处理所以未被处理的消息
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
        return DTXServerRPCResult(ret)

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
            if isinstance(aux, DTXServerRPCRawArg):
                dtx.add_auxiliary(aux.data)
            elif isinstance(aux, DTXServerRPCRawObj):
                dtx.add_auxiliary(aux.to_bytes())
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
        try:
            while self._running:
                expects_reply = False
                dtx = self._is.recv_dtx(self._cli, 1000)  # s
                if dtx is None:  # 长时间没有回调则抛出错误
                    cur = time.time()
                    if cur - last_none < 0.1:
                        raise Exception('dtx socket close')
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
                        self._channel_callbacks[2 ** 32 - dtx.channel_code](DTXServerRPCResult(dtx))
                    except:
                        traceback.print_exc()
                else:
                    try:
                        selector = selector_to_pyobject(dtx.get_selector())
                    except:
                        selector = None
                    try:
                        if selector and isinstance(selector, str) and selector in self._callbacks:
                            ret = self._callbacks[selector](DTXServerRPCResult(dtx))
                            expects_reply = True
                            if dtx.expects_reply:
                                reply = dtx.new_reply()
                                reply.set_selector(pyobject_to_selector(ret))
                                reply._payload_header.flags = 0x3
                                self._is.send_dtx(self._cli, reply)
                        elif self._unhanled_callback:
                            self._unhanled_callback(DTXServerRPCResult(dtx))
                    except:
                        traceback.print_exc()
                    if dtx.expects_reply and not expects_reply:
                        reply = dtx.new_reply()
                        reply.set_selector(b'\00' * 16)
                        reply._payload_header.flags = 0x3
                        self._is.send_dtx(self._cli, reply)
            self._receiver_exiting = True  # to block incoming calls
            for wait_key in self._sync_waits:
                self._sync_waits[wait_key]['result'] = InstrumentServiceConnectionLost
                self._sync_waits[wait_key]['event'].set()
        except Exception as E:
            log.error(E)
            self._run_callbacks(DTXEnum.NOTIFICATION, None)
            self._run_callbacks(DTXEnum.FINISHED, None)
            self.stop()

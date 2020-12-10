import argparse
import time
import traceback
from ctypes import sizeof
from threading import Thread, Event

from instrument.bpylist import archiver
from instrument.bpylist.bplistlib.readwrite import load
from instrument.dtxlib import DTXMessage, DTXMessageHeader, \
    pyobject_to_auxiliary, \
    pyobject_to_selector, selector_to_pyobject
from util.lockdown import LockdownClient


def get_usb_rpc(device=None):
    rpc = InstrumentRPC(device)
    if not rpc.init(DTXUSBTransport, device):
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
        return (self._header.channelCode, self._header.identifier)

    @property
    def header(self):
        return self._header.fragmentId == 0


class DTXClientMixin:

    def send_dtx(self, client, dtx):
        buffer = dtx.to_bytes()
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
        :param client: instrument client(C对象）
        :param length: 数据长度
        :return: 长度为 length 的 buffer, 失败时返回 None
        """
        ret = b''
        while len(ret) < length:
            l = length - len(ret)
            if l > 8192: l = 8192
            rb = client.recv(l, timeout)
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
            # print("--------", sel)
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

    def init(self, transport, arg):
        """
        初始化 instrument rpc 服务:
        成功后必须调用 deinit 反初始化
        :param device: 由DeviceService创建的device对象（C对象）
        :return: bool 是否成功
        """

        class T(transport, DTXClientMixin):
            pass

        self.lockdown = self.lockdown if self.lockdown else LockdownClient(udid=self.udid)
        if self.lockdown.ios_version.version[0] > 11:
            self._cli = self.lockdown.start_service("com.apple.instruments.remoteserver.DVTSecureSocketProxy")
        else:
            self._cli = self.lockdown.start_service("com.apple.instruments.remoteserver")
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
            print("Make Channel Error:", dtx.get_selector())
            raise RuntimeError("failed to make channel")
        self._channels[channel] = channel_id
        return channel_id

    def call(self, channel: str, selector: str, *auxiliaries):
        channel_id = self._make_channel(channel)
        ret = self._call(True, channel_id, selector, *auxiliaries)
        print("plist", ret)
        return InstrumentRPCResult(ret)

    def call_noret(self, channel: str, selector: str, *auxiliaries):
        channel_id = self._make_channel(channel)
        self._call(False, channel_id, selector, *auxiliaries)

    def _call(self, sync: bool, channel_id: int, selector: str, *auxiliaries):
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
        self._is.send_dtx(self._cli, dtx)  # TODO: protect this line with mutex
        if sync:
            param['event'].wait()
            ret = param['result']
            self._sync_waits.pop(wait_key)
            return ret

    def _receiver(self):
        last_none = 0
        while self._running:
            dtx = self._is.recv_dtx(self._cli, 2)  # s
            if dtx is None:
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

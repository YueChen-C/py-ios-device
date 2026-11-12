"""DTX (Instruments) 服务的客户端/服务端实现。

DTXClient 负责在 socket 上按 DTX 分片协议收发字节;
DTXServer 在其上实现请求-应答 (RPC)、通道消息与回调分发。
"""

import enum
import queue
import typing
from collections import defaultdict
from threading import Event, Thread

from ..util import Log
from ..util.dtx_msg import DTXMessage, InfoRequest, MessageAux, dtx_message_header, object_to_aux
from ..util.exceptions import MuxError
from ..util.variables import LOG

log = Log.getLogger(LOG.Instrument.value)

DTX_MAGIC = 0x1F3D5B79
# 通道码按 32 位无符号解析, 对端推送使用二进制补码 (channel 2 -> 0xFFFFFFFE);
# 还原通道号需用 2**32 减去该无符号值, 不能用 0xFFFFFFFF
CHANNEL_CODE_BASE = 1 << 32
REPLY_TIMEOUT = 30.0  # 等待对端应答的超时时间 (秒)
CAPABILITIES_TIMEOUT = 5.0  # 等握能力协商完成的时间 (秒)


class DTXEnum(str, enum.Enum):
    FINISHED = "finished:"


class DTXClient:
    """DTX 消息的 socket 收发, 处理分片重组。"""

    def __init__(self):
        # {channel: (header_buffer, payload_buffer)} — 保存已收到分片首片, 等待后续分片
        self._dtx_manager: typing.DefaultDict[int, typing.Tuple[bytearray, bytearray]] = {}

    def recv(self, client, length: int) -> bytearray:
        """从 socket 精确读取 length 字节, 连接断开抛 MuxError。"""
        buf = bytearray()
        while len(buf) < length:
            chunk = client.recv(length - len(buf))
            if not chunk:
                raise MuxError("socket connection close")
            buf.extend(chunk)
        log.debug(f"接收 DTX buf: {bytes(buf)}")
        return buf

    def send_dtx(self, client, dtx: DTXMessage) -> int:
        """发送一条 DTX 消息, 返回发送字节数。"""
        buffer = bytes(dtx)
        log.debug(f"发送 DTX: {buffer}")
        return client.send(buffer)

    def recv_dtx(self, client) -> DTXMessage:
        """阻塞接收一条完整 DTX 消息 (重组所有分片)。

        :raises MuxError: 连接断开或消息头校验失败
        """
        header_size = dtx_message_header.sizeof()
        channel = None
        payload = None
        while True:
            header_buffer = self.recv(client, header_size)
            header = dtx_message_header.parse(header_buffer)
            channel = header.channel

            if header.fragment_id == 0:
                if channel not in self._dtx_manager:
                    self._dtx_manager[channel] = (header_buffer, bytearray())
                if header.fragment_count > 1:
                    # 多分片消息首片只有头部, 继续收下一分片
                    continue

            body_buffer = self.recv(client, header.payload_length)
            entry = self._dtx_manager.get(channel)
            if entry is None:
                # 没有对应的首片头部, 丢弃该分片
                log.debug(f"丢弃无首片头部的 DTX 分片: channel={channel} fragment_id={header.fragment_id}")
                continue
            entry[1].extend(body_buffer)

            if header.fragment_id == header.fragment_count - 1:
                break

        header_buffer, payload = self._dtx_manager.pop(channel)
        return DTXMessage.decode(header_buffer, payload)


class DTXServer:
    """DTX RPC 服务端会话: 请求-应答、通道消息、回调分发。"""

    def __init__(self):
        self._cli = None
        self._recv_thread = None
        self._running = False
        self._callbacks = {}
        self._undefined_callback = None
        # {channel_id: callback}; 对端通知的 channel_code 是高位补 1 的负数表示
        self._channel_callbacks = {}
        self._channels = {}
        self._published_capabilities = None
        self._reply_queues: typing.DefaultDict[int, queue.Queue] = defaultdict(queue.Queue)
        self._next_identifier = 1
        self._client = DTXClient()
        self.done = Event()
        self.register()

    def register(self):
        """注册内置回调 (能力协商)。"""

        def _notifyOfPublishedCapabilities(res):
            self.done.set()
            self._published_capabilities = res.auxiliaries

        self.register_selector_callback("_notifyOfPublishedCapabilities:", _notifyOfPublishedCapabilities)

    def init(self, _cli=None):
        """初始化会话: 绑定连接并启动接收线程, 完成能力协商。

        :param _cli: 已建立的 lockdown 服务连接
        :return: self
        """
        self._cli = _cli
        self._start()
        self._call(
            True,
            0,
            "_notifyOfPublishedCapabilities:",
            {"com.apple.private.DTXBlockCompression": 0, "com.apple.private.DTXConnection": 1},
        )
        return self

    def _start(self) -> bool:
        """启动接收线程并等待能力协商完成。

        此接口为 init 内部步骤, 用户使用 init。
        """
        if self._running or not self._cli:
            return True
        self._running = True
        self._recv_thread = Thread(target=self._receiver, name="InstrumentServer", daemon=True)
        self._recv_thread.start()
        if not self.done.wait(CAPABILITIES_TIMEOUT):
            log.warning("timeout waiting capabilities")
            return False
        return True

    def stop(self):
        """停止服务: 结束接收线程并关闭连接。"""
        self._running = False
        if self._recv_thread:
            self._recv_thread = None
        if self._cli:
            self._cli.close()
            self._cli = None

    def _run_callbacks(self, event_name, data) -> bool:
        """执行已注册的事件回调, 返回是否有回调被调用。"""
        func = self._callbacks.get(event_name)
        if func:
            func(data)
            return True
        return False

    def register_selector_callback(self, selector: str, callback: typing.Callable):
        """注册 selector 消息回调。"""
        self._callbacks[selector] = callback

    def register_channel_callback(self, channel: str, callback: typing.Callable):
        """注册通道消息回调 (该通道上的推送数据)。"""
        log.debug(f"set {channel} callback ...")
        channel_id = self.make_channel(channel)
        self._channel_callbacks[channel_id] = callback

    def register_undefined_callback(self, callback: typing.Callable):
        """注册兜底回调 (未匹配到其他规则的消恩)。"""
        self._undefined_callback = callback

    def make_channel(self, channel: str) -> int:
        """按名称创建通道 (已存在则复用), 返回通道 id。"""
        if channel in self._channels:
            return self._channels[channel]
        channel_id = len(self._channels) + 1
        self._call(True, 0, "_requestChannelWithCode:identifier:", channel_id, channel)
        self._channels[channel] = channel_id
        return channel_id

    def call(self, channel: str, selector: str, *auxiliaries, timeout: float = REPLY_TIMEOUT) -> DTXMessage:
        """RPC 调用: 在通道上发送 selector 请求并同步等待应答。

        :param timeout: 等待应答的超时时间 (秒)。内存图等大响应可以调大。
        """
        channel_id = self.make_channel(channel)
        return self._call(True, channel_id, selector, *auxiliaries, timeout=timeout)

    def _reply_ack(self, data: DTXMessage):
        """回复对端的 expects_reply 消息 (空应答)。"""
        reply = DTXMessage(
            b"\x00" * 16,
            channel_code=data.channel_code,
            identifier=data.identifier,
            conversation_index=data.conversation_index + 1,
            flags=0x3,
        )
        self._client.send_dtx(self._cli, reply)

    def wait_reply(self, message_id: int, timeout: float = REPLY_TIMEOUT) -> DTXMessage:
        """阻塞等待指定 identifier 的应答消息。

        :raises MuxError: 超时或连接关闭
        """
        try:
            ret = self._reply_queues[message_id].get(timeout=timeout)
        except queue.Empty:
            raise MuxError(f"timeout waiting reply for message {message_id}")
        if ret is None:
            raise MuxError("connection closed")
        return ret

    def _call(
        self, sync: bool, channel_id: int, selector: str, *auxiliaries, timeout: float = REPLY_TIMEOUT
    ) -> typing.Optional[DTXMessage]:
        """发送一条 DTX 请求。

        :param sync: True 时同步等待应答; False 时只发送 (触发对端回调)
        :param channel_id: 通道标识
        :param selector: 请求方法名
        :param auxiliaries: 辅助参数, 由 object_to_aux 编码
        :return: sync 时返回应答消息, 否则 None
        """
        identifier = self._next_identifier
        self._next_identifier += 1
        aux = MessageAux()
        for arg in auxiliaries:
            object_to_aux(arg, aux)
        dtx = DTXMessage(
            selector,
            channel_code=channel_id,
            identifier=identifier,
            expects_reply=sync,
            auxiliaries=aux,
        )
        if any(isinstance(arg, InfoRequest) for arg in auxiliaries):
            dtx._flags = 0
        self._client.send_dtx(self._cli, dtx)
        if sync:
            return self.wait_reply(identifier, timeout=timeout)
        return None

    def _dispatch(self, dtx: DTXMessage):
        """把一条已解码的接收消息路由到应答队列 / 通道 / selector / 兜底回调。"""
        if dtx.conversation_index == 1:
            self._reply_queues[dtx.identifier].put(dtx)
            return
        if (CHANNEL_CODE_BASE - dtx.channel_code) in self._channel_callbacks:
            self._channel_callbacks[CHANNEL_CODE_BASE - dtx.channel_code](dtx)
            return
        selector = dtx.selector
        if isinstance(selector, str) and selector in self._callbacks:
            self._callbacks[selector](dtx)
        elif self._undefined_callback:
            self._undefined_callback(dtx)
        if dtx.expects_reply:
            self._reply_ack(dtx)

    def _receiver(self):
        """接收线程主循环: 收消息并分发, 断开后发出 FINISHED。"""
        try:
            while self._running:
                dtx = self._client.recv_dtx(self._cli)
                if "_channelCanceled:" in str(dtx.selector):
                    self._cli.close()
                self._dispatch(dtx)
        except MuxError as e:
            # 主动 stop() 关闭连接属于正常退出, 只有对端异常断开才需要告警
            if self._running:
                log.warning(e)
            else:
                log.debug(e)
        except Exception as e:
            log.exception(e)
        finally:
            self._run_callbacks(DTXEnum.FINISHED, None)
            self.stop()

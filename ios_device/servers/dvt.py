import enum
import queue
import typing
from collections import defaultdict
from threading import Thread, Event

from ..util import logging, Log
from ..util.dtx_msg import DTXMessage, MessageAux, dtx_message_header, object_to_aux
from ..util.exceptions import MuxError
from ..util.variables import LOG

log = Log.getLogger(LOG.Instrument.value)


class DTXEnum(str, enum.Enum):
    FINISHED = "finished:"


class DTXClient:

    def __init__(self):
        self._dtx_manager = {}

    def recv(self, client, length) -> bytes:

        buf = bytearray()
        while len(buf) < length:
            chunk = client.recv(length - len(buf))
            if not chunk:
                raise MuxError("socket connection close")
            buf.extend(chunk)
        log.debug(f'接收 DTX buf: {buf}')
        return buf

    def send_dtx(self, client, dtx):
        buffer = bytes(dtx)
        log.debug(f'发送 DTX: {buffer}')
        return client.send(buffer)

    def recv_dtx(self, client):
        """
        :param client:
        :param timeout:  (s)
        :return:
        """
        payload = bytearray()
        while True:

            header_buffer = self.recv(client, dtx_message_header.sizeof())
            if not header_buffer:
                return None
            header = dtx_message_header.parse(header_buffer)
            key = header.channel

            if header.fragment_id == 0:
                if key not in self._dtx_manager:
                    self._dtx_manager[key] = (header_buffer, payload)

                if header.fragment_count > 1:
                    continue

            body_buffer = self.recv(client, header.payload_length)
            if not body_buffer:
                break

            if not self._dtx_manager.get(key):  # if there is no header, discard it
                continue

            self._dtx_manager.get(key)[1].extend(body_buffer)

            if header.fragment_id == header.fragment_count - 1:
                break

        data = self._dtx_manager.get(key)

        self._dtx_manager.pop(key)
        return DTXMessage.decode(data[0], data[1])


class DTXServer:

    def __init__(self):
        self._cli = None
        self._recv_thread = None
        self._running = False
        self._callbacks = {}
        self._undefined_callback = None
        self._channel_callbacks = {}
        self._channels = {}
        self._receiver_exiting = False
        self._published_capabilities = None
        self._reply_queues = defaultdict(queue.Queue)
        self._next_identifier = 1
        self._client = DTXClient()
        self.done = Event()
        self.register()

    def register(self):
        def _notifyOfPublishedCapabilities(res):
            self.done.set()
            self._published_capabilities = res.auxiliaries

        self.register_selector_callback("_notifyOfPublishedCapabilities:", _notifyOfPublishedCapabilities)

    def init(self, _cli=None):
        """ 继承类
        初始化 servers 服务:
        :return: bool 是否成功
        """
        self._cli = _cli
        self._start()
        return self

    def _start(self):
        """
        启动 servers 服务, 此接口用户无需调用, 用户使用 init 接口
        :return: bool 是否成功
        """
        if self._running:
            return True
        self._running = True
        self._recv_thread = Thread(target=self._receiver, name="InstrumentServer")
        self._recv_thread.start()
        while not self.done.wait(5):
            logging.debug("[WARN] timeout waiting capabilities")
            return False
        return True

    def stop(self):
        """
        停止 servers 服务
        :return: 无返回值
        """
        self._running = False
        if self._recv_thread:
            self._recv_thread = None
        if self._cli:
            self._cli.close()
            self._cli = None

    def _run_callbacks(self, event_name, data):
        """
        Returns:
            if called
        """
        func = self._callbacks.get(event_name)
        if func:
            func(data)
            return True

    def register_selector_callback(self, selector: str, callback: typing.Callable):

        """
        :param selector:
        :param callback:
        """
        self._callbacks[selector] = callback

    def register_channel_callback(self, channel: str, callback: typing.Callable):
        """
        Return channel messages
        :param channel:
        :param callback
        """
        log.debug(f'set {channel} callback ...')
        channel_id = self.make_channel(channel)
        self._channel_callbacks[channel_id] = callback

    def register_undefined_callback(self, callback: typing.Callable):
        """
        Returns all undefined messages
        :param callback
        """
        self._undefined_callback = callback

    def make_channel(self, channel: str):
        if channel in self._channels:
            return self._channels[channel]
        channel_id = len(self._channels) + 1
        self._call(True, 0, "_requestChannelWithCode:identifier:", channel_id, channel)
        self._channels[channel] = channel_id
        return channel_id

    def call(self, channel: str, selector: str, *auxiliaries):
        channel_id = self.make_channel(channel)
        ret = self._call(True, channel_id, selector, *auxiliaries)
        return ret

    def _reply_ack(self, data):
        reply = DTXMessage()
        reply._channel_code = data.channel_code
        reply._identifier = data.identifier
        reply._conversation_index = data.conversation_index + 1
        reply._flags = 0x3
        reply._selector = b'\00' * 16
        self._client.send_dtx(self._cli, reply)

    def wait_reply(self, message_id: int, timeout=30.0) -> DTXMessage:
        ret = self._reply_queues[message_id].get(timeout=timeout)
        if ret is None:
            raise MuxError("connection closed")
        return ret

    def _call(self, sync: bool, channel_id: int, selector: str, *auxiliaries):
        """
        :param sync: 是否回调
        :param channel_id: 通道标识
        :param selector: 请求方法名称，method name
        :param auxiliaries:
        :return:
        """
        identifier = self._next_identifier
        dtx = DTXMessage()
        dtx._identifier = identifier
        dtx._channel_code = channel_id
        dtx._selector = selector
        dtx._expects_reply = sync
        aux = MessageAux()
        dtx.auxiliaries = aux
        self._next_identifier += 1
        for arg in auxiliaries:
            object_to_aux(arg, aux)
        self._client.send_dtx(self._cli, dtx)
        if sync:
            ret = self.wait_reply(identifier)
            return ret

    def _receiver(self):
        try:
            while self._running:
                dtx = self._client.recv_dtx(self._cli)
                if '_channelCanceled:' in str(dtx.selector):
                    self._cli.close()
                if dtx.conversation_index == 1:
                    self._reply_queues[dtx.identifier].put(dtx)
                elif (2 ** 32 - dtx.channel_code) in self._channel_callbacks:
                    self._channel_callbacks[(2 ** 32 - dtx.channel_code)](dtx)
                else:
                    selector = dtx.selector
                    if isinstance(selector, str) and selector in self._callbacks:
                        self._callbacks[selector](dtx)
                    elif self._undefined_callback:
                        self._undefined_callback(dtx)
                    if dtx.expects_reply:
                        self._reply_ack(dtx)

        except MuxError as E:
            log.warn(E)
        except Exception as E:
            log.exception(E)
        finally:
            self._run_callbacks(DTXEnum.FINISHED, None)
            self.stop()

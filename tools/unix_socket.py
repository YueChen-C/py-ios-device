"""
一个简单的 unix 代理工具，用于中间人劫持获取数据包，解析 iOS 与 usbmuxd 传输过程时，转换成明文数据
使用方法：

1.sudo chmod 777 /var/run/
2.sudo  mv /var/run/usbmuxd /var/run/usbmuxx
3.python /tools/unix_socket.py
4.恢复  sudo  mv /var/run/usbmuxx /var/run/usbmuxd

"""
import logging
import os
import sys
sys.path.append(os.getcwd())
import plistlib
import re
import signal
import struct
import socket
import _thread
from _ctypes import sizeof
from time import sleep
from ios_device.util.dtxlib import DTXMessage, DTXMessageHeader, \
    get_auxiliary_text, \
    selector_to_pyobject

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

HARDWARE_PLATFORM_SUB = re.compile(r'[^\w<>/ \-_0-9\"\'\\=.?!+]+').sub


def check_buf(buf,direction):
    while buf:
        cursor = 0
        if buf[4:].startswith(b'<?xml'):
            cursor = buf[0:4]
            if not cursor or len(cursor) != 4:
                return None
            cursor = struct.unpack('>L', cursor)[0]
            payload = buf[4:4 + cursor]
            cursor += 4
            if not payload:
                return None
            payload = HARDWARE_PLATFORM_SUB('', payload.decode('utf-8')).encode('utf-8')
            logging.debug(f'PlistByte:{payload}')
            data = plistlib.loads(payload)
            print(direction,'PlistData', data)
        elif buf[16:].startswith(b'<?xml'):
            cursor = buf[0:4]
            cursor = struct.unpack('I', cursor)[0]
            body = buf[4:cursor]
            version, resp, tag = struct.unpack('III', body[:0xc])
            if version == 1:
                data = body[0xc:]
                logging.debug(f'PlistByte:{data}')
                data = plistlib.loads(data)
                print(direction,'PlistData:', data)

        elif buf[4:].startswith(b'bplist00'):
            cursor = buf[0:4]
            if not cursor or len(cursor) != 4:
                return None
            cursor = struct.unpack('>L', cursor)[0]
            payload = buf[4:4 + cursor]
            cursor += 4
            if not payload:
                return None
            logging.debug(f'PlistByte:{payload}')
            data = plistlib.loads(payload)
            print(direction,'PlistData', data)

        elif buf[:4] == b'y[=\x1f':
            try:
                _message_header = DTXMessageHeader.from_buffer_copy(buf[0: sizeof(DTXMessageHeader)])
                cursor = _message_header.length + sizeof(DTXMessageHeader)
                logging.debug(f'DTXByte:{buf[:cursor]}')
                p = DTXMessage.from_bytes(buf[:cursor])
                header = p.get_selector()
                if header:
                    print(f'接收 DTX Data: header:{selector_to_pyobject(p._selector)} body:{get_auxiliary_text(p)}')
                else:
                    print(direction,'DTX buf:', buf[:cursor])
            except Exception as E:
                print(direction,'ErrorBuf:', buf)
        else:
            print(direction,'EncryptBuf', buf)
            return

        if not cursor:
            return
        buf = buf[cursor:]


def request_handler(buffer):
    return buffer


# handle remote buffer
def response_handler(buffer):
    return buffer


def receive_from(connection):
    buffer = b""
    connection.settimeout(0.01)
    try:
        while True:
            sleep(0.01)
            data = connection.recv(4096)
            if not data:
                break
            buffer += data
    except:
        pass
    return buffer


def server_loop(oldSocket, newSocket, receive_first):
    # 作为服务器监听并接受remote_client连接
    # key = '/Users/chenpeijie/.cache/pymobiledevice/be4fde24033d5a06eadbb20ad1150ad633dbb046_ssl.txt'
    # context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    # context.load_cert_chain(key, key)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(oldSocket)
    server.listen(5)
    print(f'UNIX-LISTEN: {oldSocket} fork UNIX-CONNECT: {newSocket}')
    while True:
        client_socket, addr = server.accept()
        _thread.start_new_thread(proxy_handler, (client_socket, newSocket, receive_first))


def proxy_handler(client_socket, newSocket, receive_first):
    remote_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    remote_socket.connect(newSocket)

    if receive_first:
        remote_buffer = receive_from(remote_socket)
        client_socket.send(remote_buffer)
    while True:
        # 接受来自remote_client的信息并存储在local_buffer
        # 将local_buffer的信息再发送到remote_server
        local_buffer = receive_from(client_socket)
        if len(local_buffer):
            # print("客户端发送数据:", local_buffer)
            check_buf(local_buffer,'发送 Data:')
            local_buffer = request_handler(local_buffer)
            remote_socket.send(local_buffer)
        # 接受来自remote_server的信息并存储在remote_buffer
        # 将remote_buffer的信息再发送到remote_client
        remote_buffer = receive_from(remote_socket)
        if len(remote_buffer):
            # print("客户端接收数据:", remote_buffer)
            check_buf(remote_buffer,"接收 Data:")
            remote_buffer = request_handler(remote_buffer)
            while len(remote_buffer) > 0:  # 包体过大无法发送，进行分包发送
                client_socket.send(remote_buffer[:4096])
                remote_buffer = remote_buffer[4096:]


def main():
    def sigintHandler(signum, frame):
        os.system('rm -rf /var/run/usbmuxd')
        exit()

    signal.signal(signal.SIGINT, sigintHandler)
    signal.signal(signal.SIGHUP, sigintHandler)
    signal.signal(signal.SIGTERM, sigintHandler)
    newSocket = '/var/run/usbmuxx'
    oldSocket = '/var/run/usbmuxd'
    server_loop(oldSocket, newSocket, True)
    os.system('rm -rf /var/run/usbmuxd')


if __name__ == '__main__':
    main()

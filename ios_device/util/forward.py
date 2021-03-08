"""
@Date    : 2021-03-05
@Author  : liyachao
"""

import select
import time
from threading import Thread

from ios_device.util.usbmux import USBMux
from six import PY3
from six.moves import socketserver


class SocketRelay(object):
    def __init__(self, a, b, maxbuf=65535):
        self.a = a
        self.b = b
        self.atob = ""
        self.btoa = ""
        if PY3:
            self.atob = b""
            self.btoa = b""
        self.maxbuf = maxbuf

    def handle(self):
        while True:
            rlist = []
            wlist = []
            xlist = [self.a, self.b]
            if self.atob:
                wlist.append(self.b)
            if self.btoa:
                wlist.append(self.a)
            if len(self.atob) < self.maxbuf:
                rlist.append(self.a)
            if len(self.btoa) < self.maxbuf:
                rlist.append(self.b)
            rlo, wlo, xlo = select.select(rlist, wlist, xlist)
            if xlo:
                return
            if self.a in wlo:
                n = self.a.send(self.btoa)
                self.btoa = self.btoa[n:]
            if self.b in wlo:
                n = self.b.send(self.atob)
                self.atob = self.atob[n:]
            if self.a in rlo:
                s = self.a.recv(self.maxbuf - len(self.atob))
                if not s:
                    return
                self.atob += s
            if self.b in rlo:
                s = self.b.recv(self.maxbuf - len(self.btoa))
                if not s:
                    return
                self.btoa += s


class TCPRelay(socketserver.BaseRequestHandler):

    def handle(self):
        mux = self.server.mux
        # print("Waiting for devices...")
        mux.process(0.1)
        device = self.server.device
        dsock = device.connect(self.server.rport)
        lsock = self.request
        try:
            fwd = SocketRelay(dsock, lsock, self.server.bufsize * 1024)
            fwd.handle()
        finally:
            dsock.close()
            lsock.close()


class TCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class ThreadedTCPServer(socketserver.ThreadingMixIn, TCPServer):
    pass


class ForwardPorts(Thread):
    def __init__(self, pair_ports, device_id=None, threaded=True, bufsize=128):
        """
        iOS真机设备的端口转发
        :param pair_ports: list 端口对的数组，每对端口中前一个代表远程端口，后一个代表本地端口，例如：["8100:8100", "8200:8200"]
        :param udid:
        :param threaded:
        :param bufsize:
        """
        super().__init__()
        self.pair_ports = pair_ports
        self.device_id = device_id
        self.threaded = threaded
        self.bufsize = bufsize
        self._server = None

    def forward_ports(self):

        if self.threaded:
            serverclass = ThreadedTCPServer
        else:
            serverclass = TCPServer
        try:
            for pair_port in self.pair_ports:
                rport, lport = pair_port.split(":")
                rport = int(rport)
                lport = int(lport)
                self._server = serverclass(("localhost", lport), TCPRelay)
                self._server.rport = rport
                self._server.bufsize = self.bufsize
                self._server.udid = self.device_id
                mux = USBMux()
                mux.process()
                self._server.mux = mux
                self._server.device = mux.find_device(serial=self.device_id)
                self._server.serve_forever()
        except Exception as e:
            self.stop()
            print(e)
            exit(1)

    def run(self) -> None:
        self.forward_ports()

    def stop(self):
        time.sleep(0.5)
        if self._server:
            self._server.shutdown()


if __name__ == '__main__':
    c = ForwardPorts(["8200:8200"])
    c.start()
    # c.stop()

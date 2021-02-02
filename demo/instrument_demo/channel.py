import os
import sys

sys.path.append(os.getcwd())
from threading import Event
from ios_device.servers.Instrument import InstrumentServer
from ios_device.util.dtxlib import get_auxiliary_text
from ios_device.util import logging

log = logging.getLogger(__name__)


def channels(rpc):
    rpc.init()
    print(rpc._published_capabilities)
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer()
    channels(rpc)
    rpc.deinit()

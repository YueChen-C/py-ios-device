import json
import os
import sys

sys.path.append(os.getcwd())
from ios_device.servers.Instrument import InstrumentServer
# from ios_device.util import logging

# log = logging.getLogger(__name__)


def channels(rpc):
    rpc.init()
    print(rpc._published_capabilities)

if __name__ == '__main__':
    rpc = InstrumentServer()
    channels(rpc)
    rpc.stop()

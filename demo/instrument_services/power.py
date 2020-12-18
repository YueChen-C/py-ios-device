import struct
import time
import os
import sys

sys.path.append(os.getcwd())
from instrument.RPC import get_usb_rpc
from util import logging

log = logging.getLogger(__name__)


def power(rpc):
    headers = ['startingTime', 'duration', 'level']  # DTPower
    ctx = {
        'remained': b''
    }

    def on_channel_message(res):
        log.debug(res.parsed)
        ctx['remained'] += res.parsed['data']
        cur = 0
        while cur + 3 * 8 <= len(ctx['remained']):
            log.debug("[level.dat]", dict(zip(headers, struct.unpack('>ddd', ctx['remained'][cur: cur + 3 * 8]))))
            cur += 3 * 8
            pass
        ctx['remained'] = ctx['remained'][cur:]
        # print(res.plist)
        # print(res.raw.get_selector())

    rpc.start()
    channel = "com.apple.instruments.server.services.power"
    rpc.register_channel_callback(channel, on_channel_message)
    stream_num = rpc.call(channel, "openStreamForPath:", "live/level.dat").parsed
    log.debug("open" + str(stream_num))
    var = rpc.call(channel, "startStreamTransfer:", float(stream_num)).parsed
    log.debug("start" + str(var))
    log.debug("[!] wait a few seconds, be patient...")
    time.sleep(10)
    var = rpc.call(channel, "endStreamTransfer:", float(stream_num)).parsed
    log.debug("stop" + str(var))
    rpc.stop()


if __name__ == '__main__':
    rpc = get_usb_rpc()
    power(rpc)
    rpc.deinit()

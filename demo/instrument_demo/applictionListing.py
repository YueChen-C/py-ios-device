"""
获取 app 详细列表信息
"""
import json

from ios_device.servers.DTXSever import DTXServerRPC
from ios_device.servers.Instrument import InstrumentServer


def applictionListing(rpc: DTXServerRPC):
    ret = rpc.call(
        "com.apple.instruments.server.services.device.applictionListing",
        "installedApplicationsMatching:registerUpdateToken:",
        {}, "")
    print(json.dumps(ret.parsed, indent=4))
    rpc.stop()


if __name__ == '__main__':
    rpc = InstrumentServer().init()
    applictionListing(rpc)
    rpc.stop()

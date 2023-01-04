import logging
import struct

from construct import Struct, PascalString, Int, Optional

from ios_device.util.lockdown import LockdownClient

LOCATION_STRUCT = Struct(
    status=Int,
    latitude=Optional(PascalString(Int, "utf8")),
    longitude=Optional(PascalString(Int, "utf8")),
)


class SimulateLocation(object):
    SERVICE_NAME = 'com.apple.dt.simulatelocation'

    def __init__(self, lockdown=None, udid=None, network=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown or LockdownClient(udid=udid, network=network)
        self.service = self.lockdown.start_service(self.SERVICE_NAME)

    def clear(self):
        """ stop simulation """
        self.service.sock.sendall(LOCATION_STRUCT.build({'status': 1}))

    def set(self, latitude: float, longitude: float):
        """ set simulation """
        location_byte = LOCATION_STRUCT.build({
            'status': 0,
            'latitude': str(latitude),
            'longitude': str(longitude)
        })
        self.service.sock.sendall(location_byte)

import base64
import logging
from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

from ios_device.remote.remotexpc import RemoteXPCConnection
from ios_device.servers.plist_service import PlistService
from ios_device.util import get_home_path, plistlib
from ios_device.util.exceptions import InvalidServiceError, StartServiceError, \
    PyiOSDeviceException
from ios_device.util.lockdown import LockdownClient


@dataclass
class RSDDevice:
    hostname: str
    udid: str
    product_type: str
    os_version: str


RSD_PORT = 58783


class RemoteLockdownClient(LockdownClient):
    def __init__(self, address: Tuple[str, int]):
        super().__init__(address=address)
        self.peer_info: Optional[Mapping] = None
        self.service = None

    @property
    def product_version(self) -> str:
        return self.peer_info['Properties']['OSVersion']

    @property
    def ecid(self) -> int:
        return self.peer_info['Properties']['UniqueChipID']

    def connect(self) -> None:
        self.service = RemoteXPCConnection(self.address)
        self.service.connect()
        self.peer_info = self.service.receive_response()
        self.udid = self.peer_info['Properties']['UniqueDeviceID']
        self.product_type = self.peer_info['Properties']['ProductType']
        self.svc = self.start_service('com.apple.mobile.lockdown.remote.trusted')

    def start_lockdown_service_without_checkin(self, name: str):
        return PlistService.create_tcp(self.service.address[0], self.get_service_port(name))

    def start_service(self, name: str, escrow_bag: bool = False):
        service = self.start_lockdown_service_without_checkin(name)
        checkin = {'Label': 'pyiOSDevice', 'ProtocolVersion': '2', 'Request': 'RSDCheckin'}
        if escrow_bag:
            pairing_record = plistlib.load(get_home_path(f'remote_{self.udid}.plist'))
            checkin['EscrowBag'] = base64.b64decode(pairing_record['remote_unlock_host_key'])
        response = service.plist_request(checkin)
        if response['Request'] != 'RSDCheckin':
            raise PyiOSDeviceException(f'Invalid response for RSDCheckIn: {response}. Expected "RSDCheckIn"')
        response = service.recv_plist()
        if response['Request'] != 'StartService':
            raise PyiOSDeviceException(f'Invalid response for RSDCheckIn: {response}. Expected "ServiceService"')
        return service

    def start_lockdown_developer_service(self, name, escrow_bag: bool = False):
        try:
            return self.start_lockdown_service_without_checkin(name)
        except StartServiceError:
            logging.getLogger(self.__module__).error(
                'Failed to connect to required service. Make sure DeveloperDiskImage.dmg has been mounted. '
                'You can do so using: pymobiledevice3 mounter mount'
            )
            raise

    def start_remote_service(self, name: str) -> RemoteXPCConnection:
        service = RemoteXPCConnection((self.service.address[0], self.get_service_port(name)))
        return service

    def get_service_port(self, name: str) -> int:
        """takes a service name and returns the port that service is running on if the service exists"""
        service = self.peer_info['Services'].get(name)
        if service is None:
            raise InvalidServiceError(f'No such service: {name}')
        return int(service['Port'])

    def __enter__(self) -> 'RemoteLockdownClient':
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return (f'<{self.__class__.__name__} PRODUCT:{self.product_type} VERSION:{self.product_version} '
                f'UDID:{self.udid}>')

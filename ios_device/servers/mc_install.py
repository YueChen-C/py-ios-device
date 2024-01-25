import plistlib
import logging

from ios_device.remote.remote_lockdown import RemoteLockdownClient
from ios_device.util.lockdown import LockdownClient


class MCInstallService(object):
    SERVICE_NAME = 'com.apple.mobile.MCInstall'
    RSD_SERVICE_NAME = 'com.apple.mobile.MCInstall.shim.remote'

    def __init__(self, lockdown=None, udid=None, network=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown or LockdownClient(udid=udid, network=network)
        SERVICE_NAME = self.RSD_SERVICE_NAME if isinstance(self.lockdown, RemoteLockdownClient) else self.SERVICE_NAME
        self.service = self.lockdown.start_service(SERVICE_NAME)

    def get_profile_list(self):
        self.service.send_plist({'RequestType': 'GetProfileList'})
        res = self.service.recv_plist()
        if res.get('Status', None) != 'Acknowledged':
            self.logger.error("GetProfileList error")
            self.logger.error(res)
        return res

    def install_profile(self, payload):
        self.service.send_plist({'RequestType': 'InstallProfile', 'Payload': payload})
        return self.service.recv_plist()

    def remove_profile(self, ident):
        profiles = self.get_profile_list()
        if not profiles:
            return
        if ident not in profiles['ProfileMetadata']:
            self.logger.info('Trying to remove not installed profile %s', ident)
            return
        meta = profiles['ProfileMetadata'][ident]
        data = plistlib.dumps({'PayloadType': 'Configuration',
                               'PayloadIdentifier': ident,
                               'PayloadUUID': meta['PayloadUUID'],
                               'PayloadVersion': meta['PayloadVersion']
                               })
        self.service.send_plist({'RequestType': 'RemoveProfile', 'ProfileIdentifier': data})
        return self.service.recv_plist()

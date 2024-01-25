"""

"""
import logging

from ..remote.remote_lockdown import RemoteLockdownClient
from ..util.lockdown import LockdownClient


class DiagnosticsRelayService:
    SERVICE_NAME = "com.apple.mobile.diagnostics_relay"
    RSD_SERVICE_NAME = 'com.apple.mobile.diagnostics_relay.shim.remote'

    def __init__(self, lockdown=None, udid=None, network=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown or LockdownClient(udid=udid, network=network)
        SERVICE_NAME = self.RSD_SERVICE_NAME if isinstance(self.lockdown,
                                                           RemoteLockdownClient) else self.SERVICE_NAME
        self.conn = self.lockdown.start_service(SERVICE_NAME)

    def get_battery(self, name='IOPMPowerSource'):
        ret = self.conn.plist_request({
            'Request': 'IORegistry',
            'EntryClass': name,
        })
        return ret['Diagnostics']["IORegistry"]

    def reboot(self) -> str:
        """ reboot device """
        ret = self.conn.plist_request({
            "Request": "Restart",
        })
        return ret['Status']

    def shutdown(self):
        ret = self.conn.plist_request({
            "Request": "Shutdown",
        })
        return ret['Status']
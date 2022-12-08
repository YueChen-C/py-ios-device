"""

"""
import logging

from ..util.lockdown import LockdownClient


class DiagnosticsRelayService:
    SERVICE_NAME = "com.apple.mobile.diagnostics_relay"

    def __init__(self, lockdown=None, udid=None, network=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown or LockdownClient(udid=udid, network=network)
        self.conn = self.lockdown.start_service("com.apple.mobile.diagnostics_relay")

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
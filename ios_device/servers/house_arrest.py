"""

"""
import logging

from ios_device.remote.remote_lockdown import RemoteLockdownClient
from ..servers.afc import AFCClient, AFCShell
from ..util.lockdown import LockdownClient


class HouseArrestService(AFCClient):
    SERVICE_NAME = "com.apple.mobile.house_arrest"
    RSD_SERVICE_NAME = 'com.apple.mobile.house_arrest.shim.remote'

    def __init__(self, lockdown=None, udid=None, network=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown or LockdownClient(udid=udid, network=network)
        SERVICE_NAME = self.RSD_SERVICE_NAME if isinstance(self.lockdown,
                                                           RemoteLockdownClient) else self.SERVICE_NAME
        super(HouseArrestService, self).__init__(self.lockdown, SERVICE_NAME)

    def stop_session(self):
        self.logger.info("Disconecting...")
        self.service.close()

    def send_command(self, applicationId, cmd="VendContainer"):
        self.service.send_plist({"Command": cmd, "Identifier": applicationId})
        res = self.service.recv_plist()
        if res.get("Error"):
            self.logger.error("%s : %s", applicationId, res.get("Error"))
            return False
        else:
            return True

    def shell(self, applicationId, cmd="VendContainer"):
        res = self.send_command(applicationId, cmd)
        if res:
            AFCShell(client=self).cmdloop()


if __name__ == '__main__':
    HouseArrestService().shell('cn.rongcloud.rce.autotest.xctrunner')

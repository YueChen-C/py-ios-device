import logging

from ios_device.util.lockdown import LockdownClient


class SBServiceClient(object):
    SERVICE_NAME = "com.apple.springboardservices"

    def __init__(self, lockdown=None, udid=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown if lockdown else LockdownClient(udid=udid)
        self.service = self.lockdown.start_service(self.SERVICE_NAME)

    def get_icon_state(self, format_version="2"):
        cmd = {"command": "getIconState"}
        if format_version:
            cmd["formatVersion"] = format_version

        self.service.send_plist(cmd)
        res = self.service.recv_plist()
        return res

    def set_icon_state(self, newstate={}):
        cmd = {"command": "setIconState",
               "iconState": newstate}

        self.service.send_plist(cmd)

    def get_icon_pngdata(self, bid):
        cmd = {"command": "getIconPNGData",
               "bundleId": bid}

        self.service.send_plist(cmd)
        res = self.service.recv_plist()
        pngdata = res.get("pngData")
        if res:
            return pngdata
        return None

    def get_interface_orientation(self):
        cmd = {"command": "getInterfaceOrientation"}
        self.service.send_plist(cmd)
        res = self.service.recv_plist()
        return res.get('interfaceOrientation')

    def get_wallpaper_pngdata(self):
        cmd = {"command": "getHomeScreenWallpaperPNGData"}
        self.service.send_plist(cmd)
        res = self.service.recv_plist()
        if res:
            return res.get("pngData")
        return None

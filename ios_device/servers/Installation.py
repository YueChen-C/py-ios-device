#!/usr/servers/env python
# -*- coding: utf8 -*-
#
# $Id$
#
# Copyright (c) 2012-2014 "dark[-at-]gotohack.org"
#
# This file is part of pymobiledevice
#
# pymobiledevice is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

import os
import logging

from optparse import OptionParser
from ..servers.afc import AFCClient

from ..util.lockdown import LockdownClient

client_options = {
    "SkipUninstall": False,
    "ApplicationSINF": False,
    "iTunesMetadata": False,
    "ReturnAttributes": False
}


class InstallationProxyService(object):
    SERVICE_NAME = 'com.apple.mobile.installation_proxy'

    def __init__(self, lockdown=None, udid=None, network=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown if lockdown else LockdownClient(udid=udid, network=network)
        self.service = self.lockdown.start_service(self.SERVICE_NAME)
        if not self.service:
            raise Exception("installation_proxy init error : Could not start com.apple.mobile.installation_proxy")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.service.close()

    def __enter__(self):
        return self

    def watch_completion(self, handler=None, *args):
        while True:
            z = self.service.recv_plist()
            if not z:
                break
            completion = z.get("PercentComplete")
            if completion:
                if handler:
                    self.logger.debug("calling handler")
                    handler(completion, *args)
                self.logger.info("%s %% Complete", z.get("PercentComplete"))
            if z.get("Status") == "Complete":
                self.logger.info("Success")
                return z.get("Status"), True
            if z.get('Error'):
                self.logger.info(z.get('ErrorDescription'))
                return z.get("Error"), False

        return Exception("Install Error")

    def send_cmd_for_bid(self, bid, cmd="Archive", options=None, handler=None, *args):
        cmd = {"Command": cmd,

               "ApplicationIdentifier": bid}
        if options:
            cmd.update({"ClientOptions": options})
        self.logger.info("%s : %s\n", cmd, self.watch_completion(handler, *args))

    def uninstall(self, bid, options=None, handler=None, *args):
        self.send_cmd_for_bid(bid, "Uninstall", options, handler, args)

    def install_or_upgrade(self, ipaPath, cmd="Install", options={}, handler=None, *args):
        afc = AFCClient(self.lockdown)
        self.logger.info(f"push  path {ipaPath}")
        afc.set_file_contents("/" + os.path.basename(ipaPath), open(ipaPath, "rb").read())
        cmd = {"Command": cmd,
               "ClientOptions": options,
               "PackagePath": os.path.basename(ipaPath)}

        self.service.send_plist(cmd)
        return self.watch_completion(handler, args)

    def install(self, ipaPath, options={}, handler=None, *args):
        return self.install_or_upgrade(ipaPath, "Install", options, handler, args)

    def upgrade(self, ipaPath, options={}, handler=None, *args):
        return self.install_or_upgrade(ipaPath, "Upgrade", options, handler, args)

    def check_capabilities_match(self, capabilities, options={}):
        cmd = {"Command": "CheckCapabilitiesMatch",
               "ClientOptions": options}

        if capabilities:
            cmd["Capabilities"] = capabilities

        self.service.send_plist(cmd)
        result = self.service.recv_plist().get("LookupResult")
        return result

    def browse(self, options={}, attributes=None, handler=None, *args):
        if attributes:
            options["ReturnAttributes"] = attributes

        cmd = {"Command": "Browse",
               "ClientOptions": options}

        self.service.send_plist(cmd)

        result = []
        while True:
            z = self.service.recv_plist()
            if not z:
                break

            data = z.get("CurrentList")
            if data:
                result += data

            if z.get("Status") == "Complete":
                break

        return result

    def apps_info(self, options={}):
        cmd = {"Command": "Lookup",
               "ClientOptions": options}

        self.service.send_plist(cmd)
        return self.service.recv_plist().get('LookupResult')

    def archive(self, bid, options={}, handler=None, *args):
        self.send_cmd_for_bid(bid, "Archive", options, handler, args)

    def restore_archive(self, bid, options={}, handler=None, *args):
        self.send_cmd_for_bid(bid, "Restore", options, handler, args)

    def remove_archive(self, bid, options={}, handler=None, *args):
        self.send_cmd_for_bid(bid, "RemoveArchive", options, handler, args)

    def archives_info(self, options={}):
        cmd = {"Command": "LookupArchive",
               "ClientOptions": options}
        return self.service.send_plist(cmd).get("LookupResult")

    def search_path_for_bid(self, bid):
        path = None
        for a in self.get_apps(appTypes=["User", "System"]):
            if a.get("CFBundleIdentifier") == bid:
                path = a.get("Path") + "/" + a.get("CFBundleExecutable")
        return path

    def get_apps(self, appTypes=["User"]):
        return [app for app in self.apps_info().values()
                if app.get("ApplicationType") in appTypes]

    def print_apps(self, appType=["User"]):
        for app in self.get_apps(appType):
            print(("%s : %s => %s" % (app.get("CFBundleDisplayName"),
                                      app.get("CFBundleIdentifier"),
                                      app.get("Path") if app.get("Path")
                                      else app.get("Container"))).encode('utf-8'))

    def find_bundle_id(self, bundle_id):
        for app in self.get_apps():
            if app.get('CFBundleIdentifier') == bundle_id:
                return app

    def get_apps_bid(self, appTypes=["User"]):
        return [app["CFBundleIdentifier"]
                for app in self.get_apps()
                if app.get("ApplicationType") in appTypes]

    def close(self):
        self.service.close()

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

import logging
import os
import re
import sys
from optparse import OptionParser
from sys import exit

from ios_device.remote.remote_lockdown import RemoteLockdownClient

sys.path.append(os.getcwd())
from ios_device.util.lockdown import LockdownClient

TIME_FORMAT = '%H:%M:%S'


class SyslogServer(object):
    """
    View system logs
    """
    SERVICE_NAME = "com.apple.syslog_relay"
    RSD_SERVICE_NAME = 'com.apple.syslog_relay.shim.remote'

    def __init__(self, lockdown=None, udid=None, network=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown or LockdownClient(udid=udid, network=network)
        SERVICE_NAME = self.RSD_SERVICE_NAME if isinstance(self.lockdown,
                                                           RemoteLockdownClient) else self.SERVICE_NAME
        self.c = self.lockdown.start_service(SERVICE_NAME)

    def watch(self, log_file=None, filter=None):
        """View log
        :param log_file: full path to the log file
        :param filter: filter strings
        """
        while True:
            d = self.c.recv(4096)
            d = d.decode('utf-8')
            if filter:
                procFilter = re.compile(filter, re.IGNORECASE)
                if not procFilter.search(d):
                    continue
            s = d.strip("\n\x00\x00")
            print(s)
            if log_file:
                if isinstance(log_file, str):
                    with open(log_file, 'wt') as f:
                        f.write(d.replace("\x00", ""))
                else:
                    log_file.write(d.replace("\x00", ""))


if __name__ == "__main__":
    parser = OptionParser(usage="%prog")
    parser.add_option("-u", "--udid",
                      default=False, action="store", dest="device_udid", metavar="DEVICE_UDID",
                      help="Device udid")
    parser.add_option("-p", "--process", dest="procName", default=False,
                      help="Show process log only", type="string")
    parser.add_option("-o", "--logfile", dest="logFile", default=False,
                      help="Write Logs into specified file", type="string")
    parser.add_option("-w", "--watch-time",
                      default=False, action="store", dest="watchtime", metavar="WATCH_TIME",
                      help="watchtime")
    (options, args) = parser.parse_args()

    try:
        try:
            logging.basicConfig(level=logging.INFO)
            lckdn = LockdownClient(options.device_udid)
            syslog = SyslogServer(lockdown=lckdn)
            syslog.watch(filter=options.procName, log_file=options.logFile)
        except KeyboardInterrupt:
            print("KeyboardInterrupt caught")
            raise
        else:
            pass
    except (KeyboardInterrupt, SystemExit):
        exit()

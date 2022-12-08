"""
获取崩溃日志列表，导出崩溃日志，删除崩溃日志
"""

import logging
import os

from ios_device.servers.afc import AFCCrashLog
from ios_device.servers.testmanagerd import TestManagerdLockdown
from ios_device.util.lockdown import LockdownClient


class crashLog(object):
    def __init__(self, lockdown=None, udid=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown or LockdownClient(udid=udid)
        self.crash_server = AFCCrashLog(lockdown=self.lockdown)

    def get_list(self):
        crash_list = self.crash_server.read_directory('/')
        print(crash_list)

    def delete_crash(self, name):
        status = self.crash_server.file_remove('//' + name)
        print(f'delete {name} status {status}')

    def export_crash(self, name):
        data = self.crash_server.get_file_contents('//' + name)
        local_crash_file = os.path.join(os.getcwd(), name)
        with open(local_crash_file, 'wb') as (fp):
            fp.write(data)
        print(f'export path {local_crash_file}')


if __name__ == '__main__':
    TestManagerdLockdown().init()
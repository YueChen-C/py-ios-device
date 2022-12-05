#!/usr/bin/env python3
import logging

from ios_device.util.lockdown import LockdownClient


class AmfiService:
    SERVICE_NAME = 'com.apple.amfi.lockdown'

    def __init__(self, lockdown=None, udid=None, network=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown or LockdownClient(udid=udid, network=network)

    def enable_developer_mode(self):
        """ The device will restart and enable Developer mode
        :return:
        """
        service = self.lockdown.start_service(self.SERVICE_NAME)
        resp = service.plist_request({'action': 1})
        if not resp.get('success'):
            raise Exception('enable developer mode error')
        self.logger.info('device will restart ...')

    def enable_developer_mode_turn_on(self):
        """ answer the prompt that appears after the restart with "turn on" """
        service = self.lockdown.start_service(self.SERVICE_NAME)
        resp = service.plist_request({'action': 2})
        if not resp.get('success'):
            raise Exception(f'enable_developer_mode_turn_on {resp}')


if __name__ == '__main__':
    AmfiService().enable_developer_mode()
    # AmfiService().enable_developer_mode_turn_on()

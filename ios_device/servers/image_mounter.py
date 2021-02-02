import logging
import os

from ..util.lockdown import LockdownClient


class installation_proxy(object):

    def __init__(self, lockdown=None, udid=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown if lockdown else LockdownClient(udid=udid)

        if not self.lockdown:
            raise Exception("Unable to start lockdown")
        self.service = self.lockdown.start_service("com.apple.mobile.mobile_image_mounter")
        if not self.service:
            raise Exception("installation_proxy init error : Could not start com.apple.mobile.installation_proxy")

    def lookup(self, image_type="Developer"):
        """
        Check image signature
        """
        ret = self.service.plist_request({
            "Command": "LookupImage",
            "ImageType": image_type,
        })
        if 'Error' in ret:
            raise Exception(ret['Error'])
        return ret.get('ImageSignature', [])

    def mount(self, image_path: str, image_signature: str, image_type="Developer"):
        assert os.path.isfile(image_path)
        assert os.path.isfile(image_signature)

        with open(image_signature, 'rb') as f:
            signature_content = f.read()

        ret = self.service.plist_request({
            "Command": "ReceiveBytes",
            "ImageSignature": signature_content,
            "ImageSize": os.path.getsize(image_path),
            "ImageType": image_type,
        })
        # self._check_error(ret)
        assert ret['Status'] == 'ReceiveBytesAck'

        # Send data through SSL

        chunk_size = 1 << 14
        with open(image_path, "rb") as src:
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                self.service.sock.sendall(chunk)

        ret = self.service.recv_plist()
        # self._check_error(ret)

        assert ret['Status'] == 'Complete'

        self.service.send_plist({
            "Command": "MountImage",
            "ImagePath": "/private/var/mobile/Media/PublicStaging/staging.dimag",
            "ImageSignature": signature_content,
            "ImageType": image_type,
        })
        ret = self.service.recv_plist()
        if 'DetailedError' in ret:
            if 'is already mounted at /Developer' in ret['DetailedError']:
                raise Exception("DeveloperImage is already mounted")
        # self._check_error(ret)

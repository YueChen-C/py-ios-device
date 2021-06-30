import logging
import os
import typing


class MobileImageMounter(object):

    SERVICE_NAME = 'com.apple.mobile.mobile_image_mounter'

    def __init__(self, lockdown=None, udid=None, logger=None,service=None):
        from ..util.lockdown import LockdownClient
        self.logger = logger or logging.getLogger(__name__)
        self.lockdown = lockdown if lockdown else LockdownClient(udid=udid)
        self.service = service if service else self.lockdown.start_service(self.SERVICE_NAME)

        if not self.lockdown:
            raise Exception("Unable to start lockdown")
        if not self.service:
            raise Exception("installation_proxy init error : Could not start com.apple.mobile.mobile_image_mounter")

    def lookup(self, image_type="Developer") -> typing.List[bytes]:
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

    def is_developer_mounted(self) -> bool:
        """
        Check if developer image mounted

        Raises:
            MuxError("DeviceLocked")
        """
        return len(self.lookup()) > 0

    def _check_error(self, ret: dict):
        if 'Error' in ret:
            raise Exception(ret['Error'])

    def mount(self,
              image_path: str,
              image_signature_path: str):
        """ Mount developer disk image from local files """
        assert os.path.isfile(image_path), image_path
        assert os.path.isfile(image_signature_path), image_signature_path

        with open(image_signature_path, 'rb') as f:
            signature_content = f.read()

        image_size = os.path.getsize(image_path)

        with open(image_path, "rb") as image_reader:
            return self.mount_fileobj(image_reader, image_size, signature_content)

    def mount_fileobj(self,
                      image_reader: typing.IO,
                      image_size: int,
                      signature_content: bytes,
                      image_type: str = "Developer"):

        ret = self.service.plist_request({
            "Command": "ReceiveBytes",
            "ImageSignature": signature_content,
            "ImageSize": image_size,
            "ImageType": image_type,
        })
        self._check_error(ret)
        assert ret['Status'] == 'ReceiveBytesAck'

        # Send data through SSL
        logging.info("Pushing DeveloperDiskImage.dmg")
        chunk_size = 1 << 14

        while True:
            chunk = image_reader.read(chunk_size)
            if not chunk:
                break
            self.service.sock.sendall(chunk)

        ret = self.service.recv_plist()
        self._check_error(ret)

        assert ret['Status'] == 'Complete'
        logging.info("Push complete")

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

import contextlib
import os
import plistlib
import shutil
import sys
import tempfile
import time
import uuid
import platform

import zipfile

from distutils.version import LooseVersion
from pathlib import Path
from typing import Optional, Dict, Any, Mapping

import requests

from .exceptions import PairingError, NotTrustedError, FatalPairingError, NotPairedError, CannotStopSessionError
from .exceptions import StartServiceError, InitializationError
from .plist_service import PlistService
from .ca import make_certs_and_key
from .usbmux import MuxDevice, UsbmuxdClient
from .utils import DictAttrProperty, cached_property
from .variables import LOG
from ..servers.image_mounter import MobileImageMounter
from ..util import Log, PROGRAM_NAME

__all__ = ['LockdownClient']
log = Log.getLogger(LOG.LockDown.value)


def get_app_dir(*paths) -> str:
    home = os.path.expanduser("~")
    appdir = os.path.join(home, "." + PROGRAM_NAME)
    if paths:
        appdir = os.path.join(appdir, *paths)
    os.makedirs(appdir, exist_ok=True)
    return appdir


class LockdownClient:
    label = 'pyMobileDevice'
    udid = DictAttrProperty('device_info', 'UniqueDeviceID')
    unique_chip_id = DictAttrProperty('device_info', 'UniqueChipID')
    device_id = DictAttrProperty('device_info', 'DeviceID')
    ios_version = DictAttrProperty('device_info', 'ProductVersion', LooseVersion)

    def __init__(
            self,
            udid: Optional[str] = None,
            device: Optional[MuxDevice] = None,
            cache_dir: str = '.cache/pymobiledevice',
            network=None
    ):
        self.network = network
        self.cache_dir = cache_dir
        self.record = None  # type: Optional[Dict[str, Any]]
        self.sslfile = None
        self.session_id = None
        self.host_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, platform.node())).upper()
        self.svc = PlistService(62078, udid, device, network=network)
        self.udid = self.svc.device.serial
        self.device = device
        self.network = network
        self._verify_query_type()
        self.device_info = self.get_value()
        self.device_info['UniqueDeviceID'] = self.svc.device.serial
        self.device_info['DeviceID'] = self.svc.device.device_id
        self.paired = None
        log.info(f"Connecting Device {self.svc.device.serial} ")

    def _verify_query_type(self):
        query_type = self.svc.plist_request({'Request': 'QueryType'}).get('Type')
        if query_type != 'com.apple.mobile.lockdown':
            raise InitializationError(f'Unexpected {query_type}')

    @cached_property
    def identifier(self):
        if self.udid:
            return self.udid
        elif self.unique_chip_id:
            return f'{self.unique_chip_id:x}'
        raise InitializationError('Unable to determine UDID or ECID - failing')

    def _pair(self):
        if self._validate_pairing():
            return True
        self.pair_full()
        self.svc.close()
        self.svc = PlistService(62078, self.udid, self.svc.device, network=self.network)
        if self._validate_pairing():
            return True
        raise FatalPairingError

    def _get_pair_record(self) -> Optional[Dict[str, Any]]:
        lockdown_path = _get_lockdown_dir()
        itunes_lockdown_path = lockdown_path.joinpath(f'{self.identifier}.plist')
        try:  # 如果没有 lockdown 权限，则使用自有缓存证书，建议开启 lockdown 权限，避免重复认证
            if itunes_lockdown_path.exists():
                log.debug(f'Using iTunes pair record: {itunes_lockdown_path}')
                with itunes_lockdown_path.open('rb') as f:
                    return plistlib.load(f)
        except Exception as E:
            log.debug(f'{E}')
            log.debug(f'No iTunes pairing record found for device {self.identifier}')
            log.debug('Getting pair record from usbmuxd')
        finally:
            with UsbmuxdClient() as usb:
                return usb.get_pair_record(self.udid)

    def _validate_pairing(self):
        pair_record = self._get_pair_record() or {}
        self.record = pair_record
        if self.ios_version < LooseVersion('11.0'):  # 11 以下需要双向认证
            resp = self._plist_request('ValidatePair', PairRecord=pair_record)
            if not resp or 'Error' in resp:
                log.error(f'Failed to ValidatePair: {resp}')
                return False

        self.host_id = pair_record.get('HostID', self.host_id)
        system_buid = pair_record.get('SystemBUID') or str(uuid.uuid3(uuid.NAMESPACE_DNS, platform.node())).upper()
        resp = self._plist_request('StartSession', HostID=self.host_id, SystemBUID=system_buid)
        self.session_id = resp.get('SessionID')

        if 'Error' in resp:
            if resp['Error'] == 'InvalidHostID':
                with UsbmuxdClient() as usb:
                    usb.delete_pair_record(self.udid)
                pair_record = self._get_pair_record() or self.pair_full()
                if not pair_record:
                    return False

        if resp.get('EnableSessionSSL'):
            if not pair_record:
                self.sslfile = get_home_path(self.cache_dir,f'{self.identifier}.pem')

            else:
                self.sslfile = write_home_file(
                    self.cache_dir,
                    f'{self.identifier}.pem',
                    pair_record['HostCertificate'] + b'\n' + pair_record['HostPrivateKey']
                )
            try:
                self.svc.ssl_start(self.sslfile, self.sslfile)
            except OSError:
                self.svc = PlistService(62078, self.udid, self.device, network=self.network)
                return False
        return True

    def pair_full(self):
        device_public_key = self.get_value(key='DevicePublicKey')
        wifi_address = self.get_value(key="WiFiAddress")
        with UsbmuxdClient() as usb:
            buid = usb.read_system_buid()
        if not device_public_key:
            log.error('Unable to retrieve DevicePublicKey')
            return
        log.debug('Creating host key & certificate')
        cert_pem, priv_key_pem, dev_cert_pem = make_certs_and_key(device_public_key)
        pair_record = {
            'DevicePublicKey': device_public_key,
            'DeviceCertificate': dev_cert_pem,
            'HostCertificate': cert_pem,
            'HostID': self.host_id,
            'RootCertificate': cert_pem,
            'SystemBUID': buid
        }

        pair = self.svc.plist_request({'Label': self.label,
                                       'Request': 'Pair',
                                       'PairRecord': pair_record,
                                       "ProtocolVersion": "2",
                                       "PairingOptions": {
                                           "ExtendedPairingErrors": True}
                                       })

        if pair and pair.get('Result') == 'Success' or 'EscrowBag' in pair:
            pair_record['HostPrivateKey'] = priv_key_pem
            pair_record['EscrowBag'] = pair.get('EscrowBag')
            pair_record['WiFiMACAddress'] = wifi_address
            with UsbmuxdClient() as usb:
                usb.save_pair_record(self.udid, pair_record, self.device_id)
            write_home_file(
                self.cache_dir,
                f'{self.identifier}.pem',
                pair_record['HostCertificate'] + b'\n' + pair_record['HostPrivateKey']
            )
            return pair_record
        elif pair and pair.get('Error') == 'PasswordProtected':
            self.svc.close()
            raise NotTrustedError
        else:
            log.error(pair.get('Error'))
            self.svc.close()
            raise PairingError

    def _plist_request(self, request: str, fields: Optional[Mapping[str, Any]] = None, label=True, **kwargs):
        req = {'Request': request, 'Label': self.label} if label else {'Request': request}
        if fields:
            req.update(fields)
        for k, v in kwargs.items():
            if v:
                req[k] = v
        return self.svc.plist_request(req)

    def get_value(self, domain='', key=None):
        if isinstance(key, str) and self.record and key in self.record:
            return self.record[key]
        resp = self._plist_request('GetValue', Domain=domain, Key=key)
        if resp:
            value = resp.get('Value')
            if hasattr(value, 'data'):
                return value.data
            return value
        return None

    def set_value(self, value, domain=None, key=None):
        resp = self._plist_request('SetValue', {'Value': value}, Domain=domain, Key=key)
        log.debug(f'set_value {resp}')
        if resp.get('Error'):
            log.error(f'set_value {resp}')
        return resp

    def remove_value(self, domain=None, key=None):
        resp = self._plist_request('RemoveValue', Domain=domain, Key=key)
        log.debug(f'remove_value {resp}')
        return resp

    def enable_wireless(self, enable, wireless_id=None, buddy_id=None):

        self.set_value(domain='com.apple.mobile.wireless_lockdown', key='EnableWifiConnections', value=enable)
        self.set_value(domain='com.apple.mobile.wireless_lockdown', key='EnableWifiDebugging', value=enable)
        if enable:
            if buddy_id is not None:
                # buddy_id = [str(uuid.uuid4())]
                self.set_value(domain='com.apple.mobile.wireless_lockdown', key='WirelessBuddyID', value=buddy_id)
            if wireless_id is None:
                wireless_id = ['']
            self.set_value(domain='com.apple.xcode.developerdomain', key='WirelessHosts', value=wireless_id)
        else:
            self.remove_value(domain='com.apple.xcode.developerdomain', key='WirelessHosts')

    def _start_service(self, name: str, escrow_bag=None) -> PlistService:
        if not self.paired:
            self._pair()
        elif not name:
            raise ValueError('Name must be a valid string')

        escrow_bag = self.record['EscrowBag'] if escrow_bag is True else escrow_bag
        resp = self._plist_request('StartService', Service=name, EscrowBag=escrow_bag)
        if not resp:
            raise StartServiceError(f'Unable to start service={name!r}')
        elif resp.get('Error'):
            if resp.get('Error') == 'PasswordProtected':
                raise StartServiceError(f'Unable to start service={name!r} - a password must be entered on the device')
            error = resp.get('Error')
            raise StartServiceError(f'Unable to start service={name!r} - {error}')
        log.debug(f'connect port: {resp.get("Port")}')
        plist_service = PlistService(
            resp.get('Port'), self.udid, ssl_file=self.sslfile if resp.get('EnableServiceSSL', False) else None,
            network=self.network)
        return plist_service

    @property
    def imagemounter(self):
        """
        start_service will call imagemounter, so here should call
        _unsafe_start_service instead
        """
        service = self._start_service("com.apple.mobile.mobile_image_mounter")
        return MobileImageMounter(service=service)

    def _urlretrieve(self, url, local_filename):
        """ download url to local """
        log.info("Download %s -> %s", url, local_filename)

        try:
            tmp_local_filename = local_filename + f".download-{int(time.time() * 1000)}"
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(tmp_local_filename, 'wb') as f:
                    shutil.copyfileobj(r.raw, f, length=16 << 20)
                    f.flush()
                os.rename(tmp_local_filename, local_filename)
                log.info("%r download successfully", local_filename)
        finally:
            if os.path.isfile(tmp_local_filename):
                os.remove(tmp_local_filename)

    @contextlib.contextmanager
    def _request_developer_image_dir(self):
        product_version = self.get_value('', "ProductVersion")
        log.info("ProductVersion: %s", product_version)
        major, minor = product_version.split(".")[:2]
        version = major + "." + minor

        mac_developer_dir = f"/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/DeviceSupport/{version}"
        image_path = os.path.join(mac_developer_dir, "DeveloperDiskImage.dmg")
        signature_path = image_path + ".signature"
        if os.path.isfile(image_path) and os.path.isfile(signature_path):
            yield mac_developer_dir
        else:
            local_device_support = get_app_dir("device-support")
            image_zip_path = os.path.join(local_device_support, version + ".zip")
            if not os.path.isfile(image_zip_path):
                _alias = {
                    "12.0": "12.0 (16A366).zip",
                    "12.1": "12.1 (16B91).zip",
                    "12.2": "12.2 (16E5212e).zip",
                    "12.4": "12.4 (16G73).zip",
                }
                zip_name = _alias.get(version, f"{version}.zip")
                origin_url = f"https://github.com/filsv/iPhoneOSDeviceSupport/raw/master/{zip_name}"
                mirror_url = f"https://tool.appetizer.io/iGhibli/iOS-DeviceSupport/raw/master/DeviceSupport/{zip_name}"
                log.info("Download %s -> %s", origin_url, image_zip_path)
                try:
                    self._urlretrieve(mirror_url, image_zip_path)
                except requests.HTTPError:
                    log.debug("mirror download failed, change to original url")
                    # this might be slower
                    self._urlretrieve(origin_url, image_zip_path)

            with tempfile.TemporaryDirectory() as tmpdir:
                zf = zipfile.ZipFile(image_zip_path)
                zf.extractall(tmpdir)
                yield os.path.join(tmpdir, os.listdir(tmpdir)[0])

    def mount_developer_image(self):
        """
        Raises:
            MuxError
        """
        try:
            if self.imagemounter.is_developer_mounted():
                log.info("DeveloperImage already mounted")
                return
        except Exception:  # expect: DeviceLocked
            pass

        with self._request_developer_image_dir() as _dir:  # , signature_path:
            image_path = os.path.join(_dir, "DeveloperDiskImage.dmg")
            signature_path = image_path + ".signature"
            self.imagemounter.mount(image_path, signature_path)
            log.info("DeveloperImage mounted successfully")

    def start_service(self, name: str, escrow_bag=None) -> PlistService:
        try:
            return self._start_service(name, escrow_bag)
        except StartServiceError:
            self.mount_developer_image()
            time.sleep(.5)
            return self._start_service(name, escrow_bag)

    def stop_session(self):
        if self.session_id and self.svc:
            resp = self._plist_request('StopSession', SessionID=self.session_id)
            self.session_id = None
            if not resp or resp.get('Result') != 'Success':
                raise CannotStopSessionError(resp)
            return resp

    def enter_recovery(self):
        log.debug(self.svc.plist_request({'Request': 'EnterRecovery'}))


def get_home_path(foldername: str, filename: str) -> Path:
    path = Path('~').expanduser().joinpath(foldername)
    if not path.exists():
        path.mkdir(parents=True)
    return path.joinpath(filename)


def read_home_file(foldername: str, filename: str) -> Optional[bytes]:
    path = get_home_path(foldername, filename)
    if not path.exists():
        return None
    with path.open('rb') as f:
        return f.read()


def write_home_file(foldername: str, filename: str, data: bytes) -> str:
    path = get_home_path(foldername, filename)
    log.info(f'save path :{path}')
    with path.open('wb') as f:
        f.write(data)
    return path.as_posix()


def _get_lockdown_dir():
    if sys.platform == 'win32':
        return Path(os.environ['ALLUSERSPROFILE'] + '/Apple/Lockdown/')
    else:
        return Path('/var/db/lockdown/')

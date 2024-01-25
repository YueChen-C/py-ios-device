from errno import ENOENT, ENOTDIR

from .constants import AFC_E_UNKNOWN_ERROR, AFC_ERROR_NAMES, AFC_E_OBJECT_NOT_FOUND, AFC_E_OBJECT_IS_DIR

AFC_TO_OS_ERROR_CODES = {
    AFC_E_OBJECT_NOT_FOUND: ENOENT,
    AFC_E_OBJECT_IS_DIR: ENOTDIR,
}


class PyiOSDeviceException(Exception):
    pass


class CoreDeviceError(PyiOSDeviceException):
    pass


class LockdownException(PyiOSDeviceException):
    pass


class PairingError(LockdownException):
    pass


class NotTrustedError(PairingError):
    pass


class FatalPairingError(PairingError):
    pass


class NotPairedError(LockdownException):
    pass


class CannotStopSessionError(LockdownException):
    pass


class StartServiceError(LockdownException):
    pass


class InitializationError(LockdownException):
    pass


class MuxError(PyiOSDeviceException):
    pass


class MuxVersionError(MuxError):
    pass


class NoMuxDeviceFound(MuxError):
    pass


class NoDeviceConnectedError(PyiOSDeviceException):
    pass


class InvalidServiceError(PyiOSDeviceException):
    pass


class StreamClosedError(PyiOSDeviceException):
    pass


class UserDeniedPairingError(PyiOSDeviceException):
    pass


class AccessDeniedError(PyiOSDeviceException):
    pass


class TunneldConnectionError(PyiOSDeviceException):
    pass


class iOSError(PyiOSDeviceException, OSError):
    """Generic exception for AFC errors or errors that would normally be raised by the OS"""

    def __init__(self, errno=None, afc_errno=AFC_E_UNKNOWN_ERROR, *args, **kwargs):
        errno = AFC_TO_OS_ERROR_CODES.get(afc_errno) if errno is None else errno
        # noinspection PyArgumentList
        super().__init__(errno, *args, **kwargs)
        self.afc_errno = afc_errno

    def __str__(self):
        name = AFC_ERROR_NAMES.get(self.afc_errno, 'UNKNOWN ERROR')
        return f'{self.__class__.__name__}[afc={self.afc_errno}/{name}][os={self.errno}] {self.strerror}'


class iFileNotFoundError(PyiOSDeviceException, FileNotFoundError):
    def __init__(self, *args, **kwargs):
        # noinspection PyArgumentList
        super().__init__(ENOENT, *args, **kwargs)


class iDeviceFileClosed(iOSError):
    pass


class InstrumentRPCParseError:
    def __init__(self, data=None):
        self.data = data

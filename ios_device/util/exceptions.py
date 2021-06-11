from errno import ENOENT, ENOTDIR

from .constants import AFC_E_UNKNOWN_ERROR, AFC_ERROR_NAMES, AFC_E_OBJECT_NOT_FOUND, AFC_E_OBJECT_IS_DIR

AFC_TO_OS_ERROR_CODES = {
    AFC_E_OBJECT_NOT_FOUND: ENOENT,
    AFC_E_OBJECT_IS_DIR: ENOTDIR,
}


class PyPodException(Exception):
    """Base exception class for all exceptions in PyPod"""


class LockdownException(PyPodException):
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


class MuxError(PyPodException):
    pass


class MuxVersionError(MuxError):
    pass


class NoMuxDeviceFound(MuxError):
    pass


class iOSError(PyPodException, OSError):
    """Generic exception for AFC errors or errors that would normally be raised by the OS"""

    def __init__(self, errno=None, afc_errno=AFC_E_UNKNOWN_ERROR, *args, **kwargs):
        errno = AFC_TO_OS_ERROR_CODES.get(afc_errno) if errno is None else errno
        # noinspection PyArgumentList
        super().__init__(errno, *args, **kwargs)
        self.afc_errno = afc_errno

    def __str__(self):
        name = AFC_ERROR_NAMES.get(self.afc_errno, 'UNKNOWN ERROR')
        return f'{self.__class__.__name__}[afc={self.afc_errno}/{name}][os={self.errno}] {self.strerror}'


class iFileNotFoundError(PyPodException, FileNotFoundError):
    def __init__(self, *args, **kwargs):
        # noinspection PyArgumentList
        super().__init__(ENOENT, *args, **kwargs)


class iDeviceFileClosed(iOSError):
    pass


class InstrumentRPCParseError:
    def __init__(self, data=None):
        self.data = data

"""
Some classes that can be encoded in a binary plist but don't map into
python's type hierarchy.
"""
import copy
import uuid
from datetime import datetime, timezone


class Error(Exception):
    pass


_IGNORE_UNMAPPED_KEY = "__bpylist_ignore_unmapped__"

class timestamp(float):
    """
    Represents the concept of time (in seconds) since the UNIX epoch.

    The topic of date and time representations in computers inherits many
    of the complexities of the topics of date and time representation before
    computers existed, and then brings its own revelations to the mess.

    Python seems to take a very Gregorian view of dates, but has enabled full
    madness for times.

    However, we want to store something more agnostic, something that can easily
    be used in computations and formatted for any particular collection of
    date and time conventions.

    Fortunately, the database we use, our API, and our Cocoa clients have made
    similar decisions. So to make the transmission of data to and from clients,
    we will use this class to store our agnostic representation.
    """

    unix2apple_epoch_delta = 978307200.0

    def encode_archive(obj, archive):
        "Delegate for packing timestamps back into the NSDate archive format"
        offset = obj - timestamp.unix2apple_epoch_delta
        archive.encode('NS.time', offset)

    def decode_archive(archive):
        "Delegate for unpacking NSDate objects from an Archive"
        offset = archive.decode('NS.time')
        return timestamp(timestamp.unix2apple_epoch_delta + offset)

    def __str__(self):
        return f"bpylist.timestamp {self.to_datetime().__repr__()}"

    def to_datetime(self) -> datetime:
        return datetime.fromtimestamp(self, timezone.utc)


class NSURL:
    "Delegate for packing/unpacking Url"

    def __init__(self, base, relative):
        self._base = base
        self._relative = relative

    def __eq__(self, other) -> bool:
        return self._base == other._base and self._relative == other._relative

    def __str__(self):
        return "NSURL({}, {})".format(self._base, self._relative)

    def __repr__(self):
        return self.__str__()

    def encode_archive(obj, archive):
        "Delegate for packing timestamps back into the NSDate archive format"
        archive.encode('NS.base', obj._base)
        archive.encode('NS.relative', obj._relative)

    def decode_archive(obj, archive):
        base = archive.decode('NS.base')
        relative = archive.decode('NS.relative')
        return {"$class": "NSURL", "base": base, "relative": relative}


class XCTestConfiguration:
    _default = {
        'aggregateStatisticsBeforeCrash': {
            'XCSuiteRecordsKey': {}
        },
        'automationFrameworkPath': '/Developer/Library/PrivateFrameworks/XCTAutomationSupport.framework',
        'baselineFileRelativePath': None,
        'baselineFileURL': None,
        'defaultTestExecutionTimeAllowance': None,
        'disablePerformanceMetrics': False,
        'emitOSLogs': False,
        'formatVersion': 2,  # store in UID
        'gatherLocalizableStringsData': False,
        'initializeForUITesting': True,
        'maximumTestExecutionTimeAllowance': None,
        'productModuleName': "WebDriverAgentRunner",  # set to other value is also OK
        'randomExecutionOrderingSeed': None,
        'reportActivities': True,
        'reportResultsToIDE': True,
        'systemAttachmentLifetime': 2,
        'targetApplicationArguments': [],  # maybe useless
        'targetApplicationBundleID': None,
        'targetApplicationEnvironment': None,
        'targetApplicationPath': None,
        'testApplicationDependencies': {},
        'testApplicationUserOverrides': None,
        'testBundleRelativePath': None,
        'testExecutionOrdering': 0,
        'testTimeoutsEnabled': False,
        'testsDrivenByIDE': False,
        'testsMustRunOnMainThread': True,
        'testsToRun': None,
        'testsToSkip': None,
        'treatMissingBaselinesAsFailures': False,
        'userAttachmentLifetime': 1
    }

    def __init__(self, kv: dict):
        # self._kv = kv
        assert 'testBundleURL' in kv and isinstance(kv['testBundleURL'], NSURL)
        assert 'sessionIdentifier' in kv and isinstance(
            kv['sessionIdentifier'], uuid.UUID)

        self._kv = copy.deepcopy(self._default)
        self._kv.update(kv)

    def __str__(self):
        return f"XCTestConfiguration({self._kv})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self._kv == other._kv

    def __setitem__(self, key: str, val):
        assert isinstance(key, str)
        self._kv[key] = val

    def encode_archive(objects, archive):
        for (k, v) in objects._kv.items():
            archive.encode(k, v)

    # def decode(objects: list, archive: dict):
    #     # info = ns_info.copy()
    #     # info.pop("$class")
    #     # for key in info.keys():
    #     #     idx = info[key]
    #     #     if isinstance(idx, uid):
    #     #         info[key] = _parse_object(objects, idx.data)
    #     return XCTestConfiguration()


class XCActivityRecord(dict):
    _keys = ('activityType', 'attachments', 'finish', 'start', 'title', 'uuid')

    def __repr__(self):
        attrs = []
        for key in self._keys:
            attrs.append('{}={}'.format(key, self[key]))

        return 'XCActivityRecord({})'.format(', '.join(attrs))

    def decode_archive(archive):
        ret = XCActivityRecord()
        for key in XCActivityRecord._keys:
            ret[key] = archive.decode(key)
        return ret


class NSUUID(uuid.UUID):
    def encode_archive(objects, archive):
        archive._archive_obj["NS.uuidbytes"] = objects.bytes
        # archive.encode("NS.uuidbytes", objects.bytes)

    def decode_archive(archive):
        uuidbytes = archive.decode('NS.uuidbytes')
        return NSUUID(bytes=bytes(uuidbytes))


class uid(int):
    """
    An unique identifier used by Cocoa's NSArchiver to identify a particular
    class that should be used to map an archived object back into a native
    object.
    """

    def __repr__(self):
        return f"uid({int(self)})"

    def __str__(self):
        return f"uid({int(self)})"


class FillType(object):
    """A class for 'Fill', whatever that means."""

    def __repr__(self):
        return 'Fill'


class unicode(str):
    """A class for 'Fill', whatever that means."""

    def __repr__(self):
        return self


Fill = FillType()


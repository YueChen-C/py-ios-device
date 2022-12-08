import copy
import sys
from typing import Mapping, Dict
import uuid

from datetime import datetime, timezone
from typing import Optional
from . import plistlib

import dataclasses


class Error(Exception):
    pass


_IGNORE_UNMAPPED_KEY = "__bpylist_ignore_unmapped__"


def _verify_dataclass_has_fields(dataclass, plist_obj):
    if getattr(dataclass, _IGNORE_UNMAPPED_KEY, False):
        return

    dataclass_fields = dataclasses.fields(dataclass)

    skip_fields = {'$class'}

    fields_to_verify = plist_obj.keys() - skip_fields
    fields_with_no_dots = {
        (f if not f.startswith('NS.') else 'NS' + f[3:])
        for f in fields_to_verify}
    unmapped_fields = fields_with_no_dots - {f.name for f in dataclass_fields}
    if unmapped_fields:
        raise Error(
            f"Unmapped fields: {unmapped_fields} for class {dataclass}")


class DataclassArchiver:
    """Helper to easily map python dataclasses (PEP557) to archived objects.

    To create an archiver/unarchiver just subclass the dataclass from this
    helper, for example:

    @dataclasses.dataclass
    class MyObjType(DataclassArchiver):
        int_field: int = 0
        str_field: str = ""
        float_field: float = -1.1
        list_field: list = dataclasses.field(default_factory=list)

    and then register as usually:

    archiver.update_class_map(
            {'MyObjType': MyObjType }
    )

    If you are only interested in certain fields, you can ignore unmapped
    fields, so that no exception is raised:

    @dataclasses.dataclass
    class MyObjType(DataclassArchiver, ignore_unmapped=True):
        int_field: int = 0
        str_field: str = ""
    """

    def __init_subclass__(cls, ignore_unmapped=False):
        setattr(cls, _IGNORE_UNMAPPED_KEY, ignore_unmapped)

    @staticmethod
    def encode_archive(obj, archive):
        for field in dataclasses.fields(type(obj)):
            archive_field_name = field.name
            if archive_field_name[:2] == 'NS':
                archive_field_name = 'NS.' + archive_field_name[2:]
            archive.encode(archive_field_name, getattr(obj, field.name))

    @classmethod
    def decode_archive(cls, archive):
        _verify_dataclass_has_fields(cls, archive.object)
        field_values = {}
        for field in dataclasses.fields(cls):
            archive_field_name = field.name
            if archive_field_name[:2] == 'NS':
                archive_field_name = 'NS.' + archive_field_name[2:]
            value = archive.decode(archive_field_name)
            if isinstance(value, bytearray):
                value = bytes(value)
            field_values[field.name] = value
        return cls(**field_values)


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

    @staticmethod
    def encode_archive(obj, archive):
        "Delegate for packing timestamps back into the NSDate archive format"
        offset = obj - timestamp.unix2apple_epoch_delta
        archive.encode('NS.time', offset)

    @staticmethod
    def decode_archive(archive):
        "Delegate for unpacking NSDate objects from an archiver.Archive"
        offset = archive.decode('NS.time')
        return timestamp(timestamp.unix2apple_epoch_delta + offset)

    def __str__(self):
        return f"bpylist.timestamp {self.to_datetime().__repr__()}"

    def to_datetime(self) -> datetime:
        return datetime.fromtimestamp(self, timezone.utc)


@dataclasses.dataclass()
class NSMutableData(DataclassArchiver):
    NSdata: Optional[bytes] = None

    def __repr__(self):
        return "NSMutableData(%s bytes)" % (
            'null' if self.NSdata is None else len(self.NSdata))


@dataclasses.dataclass()
class NSMutableData(DataclassArchiver):
    NSdata: Optional[bytes] = None

    def __repr__(self):
        return "NSMutableData(%s bytes)" % (
            'null' if self.NSdata is None else len(self.NSdata))


# The magic number which Cocoa uses as an implementation version.
# I don' think there were 99_999 previous implementations, I think
# Apple just likes to store a lot of zeros
NSKeyedArchiveVersion = 100_000

# Cached for convenience
NULL_UID = plistlib.UID(0)


def unarchive(plist: bytes) -> object:
    "Unpack an NSKeyedArchived byte blob into a more useful object tree."
    return Unarchive(plist).top_object()


def unarchive_file(path: str) -> object:
    """Loads an archive from a file path."""
    with open(path, 'rb') as fd:
        return unarchive(fd.read())


def archive(obj: object) -> bytes:
    "Pack an object tree into an NSKeyedArchived blob."
    return Archive(obj).to_bytes()


class ArchiverError(Exception):
    pass


class UnsupportedArchiver(ArchiverError):
    """
    Just in case we are given a regular NSArchive instead of an NSKeyedArchive,
    or if Apple introduces a new archiver and we are given some of its work.
    """

    def __init__(self, alternate):
        super().__init__(f"unsupported encoder: `{alternate}'")


class UnsupportedArchiveVersion(ArchiverError):
    def __init__(self, version):
        super().__init__(f"expected {NSKeyedArchiveVersion}, got `{version}'")


class MissingTopObject(ArchiverError):
    def __init__(self, plist):
        super().__init__(f"no top object! plist dump: {plist}")


class MissingTopObjectUID(ArchiverError):
    def __init__(self, top):
        super().__init__(f"top object did not have a UID! dump: {top}")


class MissingObjectsArray(ArchiverError):
    def __init__(self, plist):
        super().__init__(f"full plist dump: `{plist}'")


class MissingClassMetaData(ArchiverError):
    def __init__(self, index, result):
        super().__init__(f"$class had no metadata {index}: {result}")


class MissingClassName(ArchiverError):
    def __init__(self, meta):
        super().__init__(f"$class had no $classname; $class = {meta}")


class MissingClassUID(ArchiverError):
    def __init__(self, obj):
        super().__init__(f"object has no $class: {obj}")


class CircularReference(ArchiverError):
    def __init__(self, index):
        super().__init__(f"archive has a cycle with {index}")


class MissingClassMapping(ArchiverError):
    def __init__(self, name, mapping):
        super().__init__(f"no mapping for {name} in {mapping}")


class DictArchive:
    "Delegate for packing/unpacking NS(Mutable)Dictionary objects"

    @staticmethod
    def decode_archive(archive_obj):
        key_uids = archive_obj.decode('NS.keys')
        val_uids = archive_obj.decode('NS.objects')

        count = len(key_uids)
        d = dict()

        for i in range(count):
            key = archive_obj.decode_index(key_uids[i])
            val = archive_obj.decode_index(val_uids[i])
            d[key] = val

        return d


class ListArchive:
    "Delegate for packing/unpacking NS(Mutable)Array objects"

    @staticmethod
    def decode_archive(archive_obj):
        uids = archive_obj.decode('NS.objects')
        return [archive_obj.decode_index(index) for index in uids]


class SetArchive:
    "Delegate for packing/unpacking NS(Mutable)Set objects"

    @staticmethod
    def decode_archive(archive_obj):
        uids = archive_obj.decode('NS.objects')
        return {archive_obj.decode_index(index) for index in uids}


class ArchivedObject:
    """
    Stateful wrapper around Unarchive for an archived object.

    This is the object that will be passed to unarchiving delegates
    so that they can construct objects. The only useful method on
    this class is decode(self, key).
    """

    def __init__(self, obj, unarchiver):
        self.object = obj
        self._unarchiver = unarchiver

    def decode_index(self, index: plistlib.UID):
        return self._unarchiver.decode_object(index)

    def decode(self, key: str):
        return self._unarchiver.decode_key(self.object, key)


class CycleToken:
    "token used in Unarchive's unpacked_uids cache to help detect cycles"


class Unarchive:
    """
    Capable of unpacking an archived object tree in the NSKeyedArchive format.

    Apple's implementation can be found here:
    https://github.com/apple/swift-corelibs-foundation/blob/master/Foundation\
    /NSKeyedUnarchiver.swift

    Note: At this time, we support only a limited subset of circular
    references. In general, cycles in the object tree being unarchived is
    be considered forbidden by this implementation.

    In order to properly support circular references, the unarchiver needs to
    separate allocation from initialization so that it can allocate an instance
    of a class and cache the reference before passing the instance to the
    decode-specific initializer. However, doing this for certain built-in types
    is non-trivial, and I don't want to have a mess of special cases.
    """

    def __init__(self, input_bytes: bytes) -> None:
        self.input = input_bytes
        self.unpacked_uids: Dict[plistlib.UID, object] = {}
        self.top_uid = NULL_UID
        self.objects: list = []

    def unpack_archive_header(self):
        plist = plistlib.loads(self.input)

        archiver = plist.get('$archiver')
        if archiver != 'NSKeyedArchiver':
            raise UnsupportedArchiver(archiver)

        version = plist.get('$version')
        if version != NSKeyedArchiveVersion:
            raise UnsupportedArchiveVersion(version)

        top = plist.get('$top')
        if not isinstance(top, dict):
            raise MissingTopObject(plist)

        top_uid = top.get('root')
        if top_uid is None:
            raise MissingTopObjectUID(top)
        self.top_uid = top_uid

        self.objects = plist.get('$objects')
        if not isinstance(self.objects, list):
            raise MissingObjectsArray(plist)

    def class_for_uid(self, index: plistlib.UID):
        "use the UNARCHIVE_CLASS_MAP to find the unarchiving delegate of a uid"

        meta = self.objects[index.data]
        if not isinstance(meta, dict):
            raise MissingClassMetaData(index, meta)

        name = meta.get('$classname')
        if not isinstance(name, str):
            raise MissingClassName(meta)

        klass = UNARCHIVE_CLASS_MAP.get(name)
        if klass is None:
            raise MissingClassMapping(name, UNARCHIVE_CLASS_MAP)

        return klass

    def decode_key(self, obj, key):
        val = obj.get(key)
        if isinstance(val, plistlib.UID):
            return self.decode_object(val)
        return val

    def decode_object(self, index: plistlib.UID):
        # index 0 always points to the $null object, which is the archive's
        # special way of saying the value is null/nil/none
        if index == NULL_UID:
            return None

        obj = self.unpacked_uids.get(index)
        if obj == CycleToken:
            raise CircularReference(index)

        if obj is not None:
            return obj

        raw_obj = self.objects[index.data]

        # put a temp object in place, in case we have a circular
        # reference, which we do not really support
        self.unpacked_uids[index] = CycleToken

        # if obj is a (semi-)primitive type (e.g. str)
        if not isinstance(raw_obj, dict):
            self.unpacked_uids[index] = obj
            return raw_obj

        class_uid = raw_obj.get('$class')
        if class_uid is None:
            raise MissingClassUID(raw_obj)

        klass = self.class_for_uid(class_uid)
        obj = klass.decode_archive(ArchivedObject(raw_obj, self))

        self.unpacked_uids[index] = obj
        return obj

    def top_object(self):
        "recursively decode the root/top object and return the result"

        self.unpack_archive_header()
        return self.decode_object(self.top_uid)


class ArchivingObject:
    """
    Stateful wrapper around Archive for an object being archived.

    This is the object that will be passed to unarchiving delegates
    so that they can do their part in constructing the archive. The
    only useful method on this class is encode(self, key, val).
    """

    def __init__(self, archive_obj, archiver):
        self._archive_obj = archive_obj
        self._archiver = archiver

    def encode(self, key, val):
        val = self._archiver.encode(val)
        self._archive_obj[key] = val


class Archive:
    """
    Capable of packing an object tree into the NSKeyedArchive format.

    Apple's implementation can be found here:
    https://github.com/apple/swift-corelibs-foundation/blob/master/Foundation\
    /NSKeyedArchiver.swift

    Unlike our unarchiver, we are actually capable of archiving circular
    references...so, yeah.
    """

    # types which do not require the "object" encoding for an archive;
    primitive_types = [int, float, bool, str, bytes, plistlib.UID]

    # types which require no extra encoding at all, they can be inlined
    # in the archive
    inline_types = [int, float, bool]

    def __init__(self, input_obj):
        self.input = input_obj
        # cache/map class names (str) to uids
        self.class_map = {}
        # cache/map of already archived objects to uids (to avoid cycles)
        self.ref_map = {}
        # objects that go directly into the archive, always start with $null
        self.objects = ['$null']

    def uid_for_archiver(self, archiver: type) -> plistlib.UID:
        """
        Ensure the class definition for the archiver is included in the arcive.

        Non-primitive objects are encoded as a dictionary of key-value pairs;
        there is always a $class key, which has a UID value...the UID is itself
        a pointer/index which points to the definition of the class (which is
        also in the archive).

        This method makes sure that all the metadata is included in the archive
        exactly once (no duplicates class metadata).
        """

        val = self.class_map.get(archiver)
        if val:
            return val

        val = plistlib.UID(len(self.objects))
        self.class_map[archiver] = val

        # TODO: this is where we might need to include the full class ancestry;
        #       though the open source code from apple does not appear to check
        self.objects.append({
            '$classes': [archiver],
            '$classname': archiver
        })

        return val

    def encode(self, val):
        cls = val.__class__

        if cls in Archive.inline_types:
            return val

        return self.archive(val)

    def encode_list(self, objs, archive_obj):
        archiver_uid = self.uid_for_archiver('NSArray')
        archive_obj['$class'] = archiver_uid
        archive_obj['NS.objects'] = [self.archive(obj) for obj in objs]

    def encode_set(self, objs, archive_obj):
        archiver_uid = self.uid_for_archiver('NSSet')
        archive_obj['$class'] = archiver_uid
        archive_obj['NS.objects'] = [self.archive(obj) for obj in objs]

    def encode_dict(self, obj, archive_obj):
        archiver_uid = self.uid_for_archiver('NSDictionary')
        archive_obj['$class'] = archiver_uid

        keys = []
        vals = []
        for k in obj:
            keys.append(self.archive(k))
            vals.append(self.archive(obj[k]))

        archive_obj['NS.keys'] = keys
        archive_obj['NS.objects'] = vals

    def encode_top_level(self, obj, archive_obj):
        "Encode obj and store the encoding in archive_obj"

        cls = obj.__class__

        if cls == list:
            self.encode_list(obj, archive_obj)

        elif cls == dict:
            self.encode_dict(obj, archive_obj)

        elif cls == set:
            self.encode_set(obj, archive_obj)

        else:
            archiver = ARCHIVE_CLASS_MAP.get(cls)
            if archiver is None:
                raise MissingClassMapping(obj, ARCHIVE_CLASS_MAP)

            archiver_uid = self.uid_for_archiver(archiver)
            archive_obj['$class'] = archiver_uid

            archive_wrapper = ArchivingObject(archive_obj, self)
            cls.encode_archive(obj, archive_wrapper)

    def archive(self, obj) -> plistlib.UID:
        "Add the encoded form of obj to the archive, returning the UID of obj."

        if obj is None:
            return NULL_UID

        # the ref_map allows us to avoid infinite recursion caused by
        # cycles in the object graph by functioning as a sort of promise
        ref = self.ref_map.get(id(obj))
        if ref:
            return ref

        index = plistlib.UID(len(self.objects))
        self.ref_map[id(obj)] = index

        cls = obj.__class__
        if cls in Archive.primitive_types:
            self.objects.append(obj)
            return index

        archive_obj: Dict[str, object] = {}
        self.objects.append(archive_obj)
        self.encode_top_level(obj, archive_obj)

        return index

    def to_bytes(self) -> bytes:
        "Generate the archive and return it as a bytes blob"

        # avoid regenerating
        if len(self.objects) == 1:
            self.archive(self.input)

        d = {
            '$version': NSKeyedArchiveVersion,
            '$archiver': 'NSKeyedArchiver',
            '$top': {'root': plistlib.UID(1)},
            '$objects': self.objects
        }
        # pylint: disable=no-member
        return plistlib.dumps(
            d, fmt=plistlib.FMT_BINARY, sort_keys=False)  # type: ignore
        # pylint: enable=no-member


class NullArchive:

    def decode_archive(archive):
        return None


class XCTCapabilities:
    def decode_archive(archive):
        return archive.decode('capabilities-dictionary')


class DTTapMessageArchive:

    def decode_archive(archive):
        return archive.decode('DTTapMessagePlist')


class ErrorArchive:

    def decode_archive(archive):
        domain = archive.decode('NSDomain')
        userinfo = archive.decode('NSUserInfo')
        code = archive.decode('NSCode')
        return {"$class": "NSError", "domain": domain, "userinfo": userinfo, "code": code}


class ExceptionArchive:

    def decode_archive(archive):
        name = archive.decode('NS.name')
        reason = archive.decode('NS.reason')
        userinfo = archive.decode('userinfo')
        return {"$class": "NSException", "reason": reason, "userinfo": userinfo, "name": name}


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

class DTKTraceTapMessage:
    def decode_archive(archive):
        if hasattr(archive, '_object'):
            if archive._object.get('$0'):
                return archive.decode('$0')
        return archive.decode('DTTapMessagePlist')

class MutableDataArchive:
    "Delegate for packing/unpacking NSMutableData objects"

    def decode_archive(archive):
        s = archive.decode('NS.data')
        return s

class MutableStringArchive:
    "Delegate for packing/unpacking NSMutableString objects"

    def decode_archive(archive):
        s = archive.decode('NS.string')
        return s

UNARCHIVE_CLASS_MAP = {
    'NSDictionary': DictArchive,
    'NSMutableDictionary': DictArchive,
    'NSArray': ListArchive,
    'NSMutableArray': ListArchive,
    'NSSet': SetArchive,
    'NSMutableSet': SetArchive,
    'NSDate': timestamp,
    'NSNull': NullArchive,
    'NSError': ErrorArchive,
    'NSException': ExceptionArchive,
    'NSMutableString': MutableStringArchive,
    'NSMutableData': MutableDataArchive,
    "NSUUID": NSUUID,
    "NSURL": NSURL,
    "XCTestConfiguration": XCTestConfiguration,
    'XCActivityRecord': XCActivityRecord,
    'DTKTraceTapMessage': DTKTraceTapMessage,
    'XCTCapabilities': XCTCapabilities,
    'DTTapHeartbeatMessage': DTTapMessageArchive,
    'DTSysmonTapMessage': DTTapMessageArchive,
    'DTTapMessage': DTTapMessageArchive,

}

ARCHIVE_CLASS_MAP = {
    dict: 'NSDictionary',
    list: 'NSArray',
    set: 'NSSet',
    timestamp: 'NSDate',
    NSURL: 'NSURL',
    XCTestConfiguration: 'XCTestConfiguration',
    NSUUID: 'NSUUID'

}

def update_class_map(new_map: Mapping[str, type]):
    UNARCHIVE_CLASS_MAP.update(new_map)
    ARCHIVE_CLASS_MAP.update({v: k for k, v in new_map.items()})

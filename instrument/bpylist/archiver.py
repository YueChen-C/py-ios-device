from instrument.bpylist.bplistlib._types import timestamp, uid
from instrument.bpylist.bplistlib.readwrite import load
from instrument.bpylist.bplistlib.readwrite import generate

from typing import Mapping
from collections import OrderedDict

# The magic number which Cocoa uses as an implementation version.
# I don' think there were 99_999 previous implementations, I think
# Apple just likes to store a lot of zeros
NSKeyedArchiveVersion = 100_000

# Cached for convenience
null_uid = uid(0)


def unarchive(plist: bytes) -> object:
    "Unpack an NSKeyedArchived byte blob into a more useful object tree."
    return Unarchive(plist).top_object()


def unarchive_file(path: str) -> object:
    "A convenience for unarchive(plist) which loads an archive from a file for you"
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

    def decode_archive(archive):
        key_uids = archive.decode('NS.keys')
        val_uids = archive.decode('NS.objects')

        count = len(key_uids)
        d = dict()

        for i in range(count):
            key = archive._decode_index(key_uids[i])
            val = archive._decode_index(val_uids[i])
            d[key] = val

        return d


class MutableStringArchive:
    "Delegate for packing/unpacking NSMutableString objects"

    def decode_archive(archive):
        s = archive.decode('NS.string')
        return s


class MutableDataArchive:
    "Delegate for packing/unpacking NSMutableData objects"

    def decode_archive(archive):
        s = archive.decode('NS.data')
        return s


class ListArchive:
    "Delegate for packing/unpacking NS(Mutable)Array objects"

    def decode_archive(archive):
        uids = archive.decode('NS.objects')
        return [archive._decode_index(index) for index in uids]


class SetArchive:
    "Delegate for packing/unpacking NS(Mutable)Set objects"

    def decode_archive(archive):
        uids = archive.decode('NS.objects')
        return set([archive._decode_index(index) for index in uids])


class NullArchive:

    def decode_archive(archive):
        return None


class TODOArchive:

    def decode_archive(archive):
        return "!!! TODO !!!"


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


class ArchivedObject:
    """
    Stateful wrapper around Unarchive for an archived object.

    This is the object that will be passed to unarchiving delegates
    so that they can construct objects. The only useful method on
    this class is decode(self, key).
    """

    def __init__(self, obj, unarchiver):
        self._object = obj
        self._unarchiver = unarchiver

    def _decode_index(self, index: uid):
        return self._unarchiver.decode_object(index)

    def decode(self, key: str):
        return self._unarchiver.decode_key(self._object, key)


class CycleToken:
    "token used in Unarchive's unpacked_uids cache to help detect cycles"
    pass


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

    def __init__(self, input: bytes):
        self.input = input
        self.unpacked_uids = {}
        self.top_uid = null_uid
        self.objects = None

    def unpack_archive_header(self):
        plist = load(self.input)
        archiver = plist.get('$archiver')
        if archiver != 'NSKeyedArchiver':
            raise UnsupportedArchiver(archiver)

        version = plist.get('$version')
        if version != NSKeyedArchiveVersion:
            raise UnsupportedArchiveVersion(version)

        top = plist.get('$top')
        if not isinstance(top, dict):
            raise MissingTopObject(plist)

        self.top_uid = top.get('root')
        if not isinstance(self.top_uid, uid):
            raise MissingTopObjectUID(top)

        self.objects = plist.get('$objects')
        if not isinstance(self.objects, list):
            raise MissingObjectsArray(plist)

    def class_for_uid(self, index: uid):
        "use the UNARCHIVE_CLASS_MAP to find the unarchiving delegate of a uid"

        meta = self.objects[index]
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
        if isinstance(val, uid):
            return self.decode_object(val)
        return val

    def decode_object(self, index: uid):
        # index 0 always points to the $null object, which is the archive's
        # special way of saying the value is null/nil/none
        if index == 0:
            return None
        # print("decode index:", index)
        obj = self.unpacked_uids.get(index)
        if obj == CycleToken:
            raise CircularReference(index)

        if obj is not None:
            return obj

        raw_obj = self.objects[index]
        # print(raw_obj)
        # put a temp object in place, in case we have a circular
        # reference, which we do not really support
        self.unpacked_uids[index] = CycleToken

        # if obj is a (semi-)primitive type (e.g. str)
        if not isinstance(raw_obj, dict):
            self.unpacked_uids[index] = raw_obj
            return raw_obj

        class_uid = raw_obj.get('$class')
        if not isinstance(class_uid, uid):
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
    primitive_types = [int, float, bool, str, bytes, uid]

    # types which require no extra encoding at all, they can be inlined
    # in the archive
    inline_types = [int, float, bool]

    def __init__(self, input):
        self.input = input
        # cache/map class names (str) to uids
        self.class_map = {}
        # cache/map of already archived objects to uids (to avoid cycles)
        self.ref_map = {}
        # objects that go directly into the archive, always start with $null
        self.objects = ['$null']

    def uid_for_archiver(self, archiver: type) -> uid:
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

        val = uid(len(self.objects))
        self.class_map[archiver] = val

        # TODO: this is where we might need to include the full class ancestry;
        #       though the open source code from apple does not appear to check
        self.objects.append({'$classes': [archiver], '$classname': archiver})

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

    def archive(self, obj) -> uid:
        "Add the encoded form of obj to the archive, returning the UID of obj."

        if obj is None:
            return null_uid

        # the ref_map allows us to avoid infinite recursion caused by
        # cycles in the object graph by functioning as a sort of promise
        ref = self.ref_map.get(id(obj))
        if ref:
            return ref

        index = uid(len(self.objects))
        self.ref_map[id(obj)] = index

        cls = obj.__class__
        if cls in Archive.primitive_types:
            self.objects.append(obj)
            return index

        archive_obj = {}
        self.objects.append(archive_obj)
        self.encode_top_level(obj, archive_obj)

        return index

    def to_bytes(self) -> bytes:
        "Generate the archive and return it as a bytes blob"

        # avoid regenerating
        if len(self.objects) == 1:
            self.archive(self.input)

        d = {'$archiver': 'NSKeyedArchiver',
             '$version': NSKeyedArchiveVersion,
             '$objects': self.objects,
             '$top': {'root': uid(1)}
             }
        d2 = OrderedDict()
        d2['$version'] = d['$version']
        d2['$archiver'] = d['$archiver']
        d2['$top'] = d['$top']
        d2['$objects'] = d['$objects']
        return generate(d)


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
    'DTSysmonTapMessage': TODOArchive,
    'NSMutableData': MutableDataArchive,
}

ARCHIVE_CLASS_MAP = {
    dict: 'NSDictionary',
    list: 'NSArray',
    set: 'NSSet',
    timestamp: 'NSDate'
}


def update_class_map(new_map: Mapping[str, type]):
    UNARCHIVE_CLASS_MAP.update(new_map)
    ARCHIVE_CLASS_MAP.update({v: k for k, v in new_map.items()})

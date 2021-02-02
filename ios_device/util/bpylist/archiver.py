
from .bplistlib import generate
from .bplistlib import load
from ._types import timestamp, uid, NSMutableData, NSURL, XCTestConfiguration, NSUUID, XCActivityRecord
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


class DTKTraceTapMessage:
    def decode_archive(archive):
        if archive._object.get('$0'):
            s = archive.decode('$0')
        else:
            s = archive.decode('DTTapMessagePlist')
        return s


class DTSysmonTapMessage:
    def decode_archive(archive):
        s = archive.decode('$0')
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

class XCTCapabilities:
    def decode_archive(archive):
        return archive.decode('capabilities-dictionary')

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
        self.objects.append({'$classes': [archiver, 'NSObject'], '$classname': archiver})

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
    "NSUUID": NSUUID,
    "NSURL": NSURL,
    "XCTestConfiguration": XCTestConfiguration,
    'XCActivityRecord': XCActivityRecord,
    'DTKTraceTapMessage': DTKTraceTapMessage,
    'XCTCapabilities':NullArchive

}

ARCHIVE_CLASS_MAP = {
    dict: 'NSDictionary',
    list: 'NSArray',
    set: 'NSSet',
    timestamp: 'NSDate',
    NSMutableData: 'NSMutableData',
    NSURL: 'NSURL',
    XCTestConfiguration: 'XCTestConfiguration',
    NSUUID: 'NSUUID'

}


def update_class_map(new_map: Mapping[str, type]):
    UNARCHIVE_CLASS_MAP.update(new_map)
    ARCHIVE_CLASS_MAP.update({v: k for k, v in new_map.items()})


if __name__ == '__main__':
    pass
    # buf2 = b'bplist00\xd4\x01\x02\x03\x04\x05\x06|\x7fY$archiverX$objectsT$topX$version_\x10\x0fNSKeyedArchiver\xaf\x10\x14\x07\x08EKSTX[]8^_beikqruyU$null\xdf\x10"\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./01121345633789:;<=>?@A113BC1DV$class_\x10\x1eaggregateStatisticsBeforeCrash_\x10\x17automationFrameworkPath_\x10\x18baselineFileRelativePath_\x10\x0fbaselineFileURL_\x10!defaultTestExecutionTimeAllowance_\x10\x19disablePerformanceMetricsZemitOSLogs]formatVersion_\x10\x1cgatherLocalizableStringsData_\x10\x16initializeForUITesting_\x10!maximumTestExecutionTimeAllowance_\x10\x11productModuleName_\x10\x1brandomExecutionOrderingSeed_\x10\x10reportActivities_\x10\x12reportResultsToIDE_\x10\x11sessionIdentifier_\x10\x18systemAttachmentLifetime_\x10\x1atargetApplicationArguments_\x10\x19targetApplicationBundleID_\x10\x1ctargetApplicationEnvironment_\x10\x15targetApplicationPath_\x10\x1btestApplicationDependencies_\x10\x1ctestApplicationUserOverrides_\x10\x16testBundleRelativePath]testBundleURL_\x10\x15testExecutionOrdering_\x10\x13testTimeoutsEnabled_\x10\x10testsDrivenByIDE_\x10\x18testsMustRunOnMainThreadZtestsToRun[testsToSkip_\x10\x1ftreatMissingBaselinesAsFailures_\x10\x16userAttachmentLifetime\x80\x02\x80\x03\x80\x08\x80\x00\x80\x00\x80\x00\x08\x80\t\t\x80\x00\x80\n\x80\x00\x80\x12\x10\x02\x80\x0b\x80\x00\x80\x00\x80\x00\x80\r\x80\x00\x80\x00\x80\x0f\x10\x00\x80\x00\x80\x00\x10\x01\xd2FGHIX$classesZ$classname\xa2IJ_\x10\x13XCTestConfigurationXNSObject\xd3\tLMNOQWNS.keysZNS.objects\x80\x07\xa1P\x80\x04\xa1R\x80\x05_\x10\x11XCSuiteRecordsKey\xd3\tLMUVW\x80\x06\xa0\xa0\xd2FGYZ\xa2ZJ\\NSDictionary\xd2FG\\Z\xa2ZJ_\x10C/Developer/Library/PrivateFrameworks/XCTAutomationSupport.framework_\x10\x14WebDriverAgentRunner\xd2\tM`a\x80\x0c\xa0\xd2FGcd\xa2dJWNSArray\xd3\tLMfgh\x80\x0e\xa0\xa0\xd2FGjZ\xa2ZJ\xd3\tlmnopWNS.base[NS.relative\x80\x11\x80\x00\x80\x10_\x10\x9afile:///private/var/containers/Bundle/Application/27EE0483-4045-468C-945D-0D409E1C4B47/WebDriverAgentRunner-Runner.app/PlugIns/WebDriverAgentRunner.xctest\xd2FGst\xa2tJUNSURL\xd2\tvwx\\NS.uuidbytes\x80\x13O\x10\x10\x95\x03\xe5\xd4\x82\xc7G7\xb6\x14-\x94DX\x82\xcb\xd2FGz{\xa2{JVNSUUID\xd1}~Troot\x80\x01\x12\x00\x01\x86\xa0\x00\x08\x00\x11\x00\x1b\x00$\x00)\x002\x00D\x00[\x00a\x00\xa8\x00\xaf\x00\xd0\x00\xea\x01\x05\x01\x17\x01;\x01W\x01b\x01p\x01\x8f\x01\xa8\x01\xcc\x01\xe0\x01\xfe\x02\x11\x02&\x02:\x02U\x02r\x02\x8e\x02\xad\x02\xc5\x02\xe3\x03\x02\x03\x1b\x03)\x03A\x03W\x03j\x03\x85\x03\x90\x03\x9c\x03\xbe\x03\xd7\x03\xd9\x03\xdb\x03\xdd\x03\xdf\x03\xe1\x03\xe3\x03\xe4\x03\xe6\x03\xe7\x03\xe9\x03\xeb\x03\xed\x03\xef\x03\xf1\x03\xf3\x03\xf5\x03\xf7\x03\xf9\x03\xfb\x03\xfd\x03\xff\x04\x01\x04\x03\x04\x05\x04\x07\x04\t\x04\x0e\x04\x17\x04"\x04%\x04;\x04D\x04K\x04S\x04^\x04`\x04b\x04d\x04f\x04h\x04|\x04\x83\x04\x85\x04\x86\x04\x87\x04\x8c\x04\x8f\x04\x9c\x04\xa1\x04\xa4\x04\xea\x05\x01\x05\x06\x05\x08\x05\t\x05\x0e\x05\x11\x05\x19\x05 \x05"\x05#\x05$\x05)\x05,\x053\x05;\x05G\x05I\x05K\x05M\x05\xea\x05\xef\x05\xf2\x05\xf8\x05\xfd\x06\n\x06\x0c\x06\x1f\x06$\x06\'\x06.\x061\x066\x068\x00\x00\x00\x00\x00\x00\x02\x01\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06='  # c = load(buf)

    # xctest_content = archive(XCTestConfiguration({
    #     "testBundleURL": NSURL(None, "file://" + '/private/var/containers/Bundle/Application/27EE0483-4045-468C-945D-0D409E1C4B47/WebDriverAgentRunner-Runner.app' + "/PlugIns/WebDriverAgentRunner.xctest"),
    #     "sessionIdentifier": NSUUID(bytes=os.urandom(16), version=4),
    # }))
    # c = archive(obj)
    # print(c)

    print(unarchive(

        b'bplist00\xd4\x01\x02\x03\x04\x05pqrX$objectsX$versionY$archiverT$top\xaf\x10*\x06\x07\x14\x15\x16\x17\x18\x19\x1a\x1e()*+,-.456789:;<CDHLMSWZ\x19^bcfimnU$null\xd3\x08\t\n\x0b\x0c\x10V$classWNS.keysZNS.objects\x80)\xa3\r\x0e\x0f\x80\x02\x80\x04\x80\x05\xa3\x11\x12\x13\x80\x06\x80\x08\x80(RurRbmRtcRrp\x11\x01\xf4\x10\x00\xd2\x08\n\x1b\x1c\x80 \xa1\x1d\x80\t\xd3\x08\t\n\x1f $\x80\'\xa3!"#\x80\n\x80\r\x80\x0f\xa3%&\'\x80\x10\x80\x1d\x80&Tkdf2ScsdSkdfRtkRtaTuuid\xd2\x08\n/0\x80\x19\xa3123\x80\x11\x80\x14\x80\x18\x12%\x99\x00\x00\x12\x85\x02\x00\x00\x121\xca\x00\x00\x121\xb0\x00\x00\x12\x85\x01\x00\x00\x12\x85\xc0\x00\x00\x12\x85 \x00\x00\x121\x80\x01\x08\xd2=>?@Z$classnameX$classes\\NSMutableSet\xa3?ABUNSSetXNSObject\x10\x80\xd2\x08EFGYNS.string\x80\x1c_\x10\x82<events><event type="KDebug" class="49" subclass="176" code="*"/><event type="KDebug" class="49" subclass="128" code=""/></events>\xd2=>IJ_\x10\x0fNSMutableString\xa3IKBXNSString\x10\x03\xd2\x08\nNO\x80%\xa3PQR\x80\x1f\x80!\x80#\xd2\x08\nTU\x80 \xa1V\x80\x1d\xd2=>XYWNSArray\xa2XB\xd2\x08\n[\\\x80 \xa1]\x80"\xd2\x08\n_`\x80 \xa1a\x80$\x10\x02\xd2=>de^NSMutableArray\xa3dXB\xd2\x08Egh\x80\x1c_\x10$2C46B61A-CDA9-4D59-B901-22E28B08C260\xd2=>jk_\x10\x13NSMutableDictionary\xa3jlB\\NSDictionary\x10\n\xd2=>lo\xa2lB\x12\x00\x01\x86\xa0_\x10\x0fNSKeyedArchiver\xd1stTroot\x80\x01\x00\x08\x00\x11\x00\x1a\x00#\x00-\x002\x00_\x00e\x00l\x00s\x00{\x00\x86\x00\x88\x00\x8c\x00\x8e\x00\x90\x00\x92\x00\x96\x00\x98\x00\x9a\x00\x9c\x00\x9f\x00\xa2\x00\xa5\x00\xa8\x00\xab\x00\xad\x00\xb2\x00\xb4\x00\xb6\x00\xb8\x00\xbf\x00\xc1\x00\xc5\x00\xc7\x00\xc9\x00\xcb\x00\xcf\x00\xd1\x00\xd3\x00\xd5\x00\xda\x00\xde\x00\xe2\x00\xe5\x00\xe8\x00\xed\x00\xf2\x00\xf4\x00\xf8\x00\xfa\x00\xfc\x00\xfe\x01\x03\x01\x08\x01\r\x01\x12\x01\x17\x01\x1c\x01!\x01&\x01+\x016\x01?\x01L\x01P\x01V\x01_\x01a\x01f\x01p\x01r\x01\xf7\x01\xfc\x02\x0e\x02\x12\x02\x1b\x02\x1d\x02"\x02$\x02(\x02*\x02,\x02.\x023\x025\x027\x029\x02>\x02F\x02I\x02N\x02P\x02R\x02T\x02Y\x02[\x02]\x02_\x02a\x02f\x02u\x02y\x02~\x02\x80\x02\xa7\x02\xac\x02\xc2\x02\xc6\x02\xd3\x02\xd5\x02\xda\x02\xdd\x02\xe2\x02\xf4\x02\xf7\x02\xfc\x00\x00\x00\x00\x00\x00\x02\x01\x00\x00\x00\x00\x00\x00\x00u\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xfe'

    ))

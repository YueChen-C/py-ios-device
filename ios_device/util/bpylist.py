from ._types import timestamp, uid, NSURL, XCTestConfiguration, NSUUID, XCActivityRecord
from ._types import uid, Fill, FillType, unicode

from typing import Mapping

from collections import OrderedDict

# The magic number which Cocoa uses as an implementation version.
# I don' think there were 99_999 previous implementations, I think
# Apple just likes to store a lot of zeros
NSKeyedArchiveVersion = 100_000

null_uid = uid(0)
# encoding: utf-8
import plistlib
from datetime import datetime
from struct import pack, unpack
from time import mktime


class BooleanHandler(object):
    """Handler for boolean types in a binary plist."""

    def __init__(self):
        self.type_number = 0
        self.types = (bool, type(None), FillType)
        self.integer_to_boolean = {0: None, 8: False, 9: True, 15: Fill}
        self.boolean_to_integer = dict(zip(self.integer_to_boolean.values(),
                                           self.integer_to_boolean.keys()))

    def get_object_length(self, boolean):
        """Return the object length for a boolean."""
        return self.boolean_to_integer[boolean]

    def get_byte_length(self, object_length):
        """The byte length for a boolean is always zero."""
        return 0

    def encode_body(self, string, object_length):
        """Return an empty string."""
        return b''

    def decode_body(self, raw, object_length):
        """Return the decoded boolean value."""
        return self.integer_to_boolean[object_length]


class IntegerHandler(object):
    """Handler class for integers."""

    def __init__(self):
        self.type_number = 1
        self.formats = ('B', '>H', '>L', '>Q')
        self.types = int

    def get_object_length(self, integer):
        """Return the object length for an unsigned integer."""
        bit_lengths = [8 * 2 ** x for x in range(4)]
        limits = [2 ** bit_length for bit_length in bit_lengths]
        for index, limit in enumerate(limits):
            if index == 0:
                if 0 <= integer <= limit:
                    return index
            else:
                if limits[index - 1] < integer <= limit:
                    return index
        raise ValueError

    def get_byte_length(self, object_length):
        """Calculate the byte length from the object length for a number."""
        return 1 << object_length

    def encode_body(self, value, object_length):
        """Pack the given number appropriately for the object length."""
        return pack(self.formats[object_length], value)

    def decode_body(self, raw, object_length):
        """Unpack the encoded number appropriately for the object length."""
        return unpack(self.formats[object_length], raw)[0]


class FloatHandler(IntegerHandler):
    """Handler class for floats. Subclass of the integer handler."""

    def __init__(self):
        IntegerHandler.__init__(self)
        self.type_number = 2
        self.formats = (None, None, '>f', '>d')
        self.types = float

    def get_object_length(self, float_):
        """Return the object length for a float."""
        single_max = (2 - 2 ** (-23)) * (2 ** 127)
        single_min = 2 ** -126
        double_max = (2 - 2 ** (-52)) * (2 ** 1023)
        double_min = 2 ** -1022
        if (-single_max < float_ < single_min or
                single_min < float_ < single_max):
            return 2
        elif (-double_max < float_ < double_min or
              double_min < float_ < double_max):
            return 3
        raise ValueError

    def encode_body(self, float_, object_length):
        body = IntegerHandler.encode_body(self, float_, object_length)
        return body[::-1]

    def decode_body(self, raw, object_length):
        return IntegerHandler.decode_body(self, raw, object_length)


class DateHandler(FloatHandler):
    """
    Handler class for dates. Subclass of the float handler because dates are
    stored internally as the floating point number of seconds since the epoch.
    """

    def __init__(self):
        FloatHandler.__init__(self)
        self.type_number = 3
        # seconds between 1 Jan 1970 and 1 Jan 2001
        self.epoch_adjustment = 978307200.0
        self.types = datetime

    def get_object_length(self, date):
        return 3

    def encode_body(self, date, object_length):
        seconds = self.convert_to_seconds(date)
        return FloatHandler.encode_body(self, seconds, object_length)

    def decode_body(self, raw, object_length):
        seconds = FloatHandler.decode_body(self, raw, object_length)
        return self.convert_to_date(seconds)

    def convert_to_seconds(self, date):
        """Convert a datetime object to seconds since 1 Jan 2001."""
        seconds = mktime(date.timetuple())
        return seconds - self.epoch_adjustment

    def convert_to_date(self, seconds):
        """Convert seconds since 1 Jan 2001 to a datetime object."""
        seconds += self.epoch_adjustment
        return datetime.fromtimestamp(seconds)


class ByteArrayHander(object):
    """Handler class for arbitrary binary data. Uses plistlib.Data."""

    def __init__(self):
        self.type_number = 4
        # this is ugly but maintains interop with plistlib.
        self.types = type(bytearray(b''))

    def get_object_length(self, data):
        """Get the length of the data stored inside the Data object."""
        return len(data.data)

    def get_byte_length(self, object_length):
        """Return the object length."""
        return object_length

    def encode_body(self, data, object_length):
        """Get the binary data from the Data object."""
        return data.data

    def decode_body(self, raw, object_length):
        """Store the binary data in a Data object."""
        return bytearray(raw)


class BytesHander(object):
    """Handler class for arbitrary binary data. Uses plistlib.Data."""

    def __init__(self):
        self.type_number = 4
        # this is ugly but maintains interop with plistlib.
        self.types = bytes

    def get_object_length(self, data):
        """Get the length of the data stored inside the Data object."""
        return len(data)

    def get_byte_length(self, object_length):
        """Return the object length."""
        return object_length

    def encode_body(self, data, object_length):
        """Get the binary data from the Data object."""
        return data

    def decode_body(self, raw, object_length):
        """Store the binary data in a Data object."""
        return bytearray(raw)


class StringHandler(object):
    """Handler class for strings."""

    def __init__(self):
        self.type_number = 5
        self.encoding = 'ascii'
        self.types = str

    def get_object_length(self, string):
        """Return the length of the string."""
        return len(string)

    def get_byte_length(self, object_length):
        """Return the object length."""
        return object_length

    def encode_body(self, string, object_length):
        """Return the encoded version of string, according to self.encoding."""
        return string.encode(self.encoding)

    def decode_body(self, string, object_length):
        """Return string."""
        return string


class UnicodeStringHandler(StringHandler):
    """Handler class for unicode strings. Subclass of the string handler."""

    def __init__(self):
        StringHandler.__init__(self)
        self.type_number = 6
        self.encoding = 'utf_16_be'
        self.types = unicode

    def get_byte_length(self, object_length):
        """Return twice the object length."""
        return object_length * 2

    def decode_body(self, raw, object_length):
        """Decode the raw string according to self.encoding."""
        return raw.decode(self.encoding)


class UIDHandler(IntegerHandler):
    """Handler class for UIDs. Subclass of the integer Handler."""

    def __init__(self):
        IntegerHandler.__init__(self)
        self.type_number = 8
        self.formats = ('B', '>H', '>L', '>Q')
        self.types = uid

    def get_object_length(self, uid):
        """Return the object length for an integer."""
        bit_lengths = [8 * 2 ** x for x in range(4)]
        limits = [2 ** bit_length for bit_length in bit_lengths]
        for index, limit in enumerate(limits):
            if index == 0:
                if 0 <= uid <= limit:
                    return index
            else:
                if limits[index - 1] < uid <= limit:
                    return index
        raise ValueError

    def encode_body(self, uid, object_length):
        """Get the integer value of the UID object, and encode that."""
        value = int(uid)
        return IntegerHandler.encode_body(self, value, object_length)

    def decode_body(self, raw, object_length):
        """Decode an integer value and put in a UID object."""
        value = IntegerHandler.decode_body(self, raw, object_length)
        return uid(value)


class ArrayHandler(object):
    """Handler class for arrays."""

    def __init__(self, object_handler):
        self.type_number = 0xa
        self.types = list
        self.object_handler = object_handler
        self.formats = (None, 'B', 'H')
        self.endian = '>'
        self.format = None
        self.reference_size = None

    def get_object_length(self, array):
        """Return the length of the list given."""
        return len(array)

    def get_byte_length(self, object_length):
        """Return the object length times the reference size."""
        return object_length * self.reference_size

    def encode_body(self, array, object_length):
        """Encode the flattened array as a single reference list."""
        format_ = self.endian + self.format * len(array)
        encoded = pack(format_, *array)
        return encoded

    def decode_body(self, raw, object_length):
        """Decode the reference list into a flattened array."""
        format_ = self.endian + self.format * object_length
        array = unpack(format_, raw)
        return list(array)

    def set_reference_size(self, reference_size):
        """Save the given reference size, and set self.format appropriately."""
        self.reference_size = reference_size
        self.format = self.formats[reference_size]

    def flatten(self, array, objects):
        """Flatten the array into a list of references."""
        return flatten_object_list(array, objects)

    def unflatten(self, array, objects):
        """Unflatten the list of references into a list of objects."""
        return unflatten_reference_list(array, objects, self.object_handler)

    def collect_children(self, array, objects):
        """Collect all the items in the array."""
        for item in array:
            self.object_handler.collect_objects(item, objects)


class DictionaryHandler(ArrayHandler):
    """Handler class for dictionaries. Subclasses the container handler."""

    def __init__(self, object_handler):
        ArrayHandler.__init__(self, object_handler)
        self.type_number = 0xd
        self.types = dict

    def get_byte_length(self, object_length):
        """Return twice the object length times the reference size."""
        return ArrayHandler.get_byte_length(self, object_length) * 2

    def encode_body(self, dictionary, object_length):
        """Encode the flattened dictionary as two reference lists."""
        keys = ArrayHandler.encode_body(self, dictionary.keys(), object_length)
        values = ArrayHandler.encode_body(self, dictionary.values(),
                                          object_length)
        return keys + values

    def decode_body(self, raw, object_length):
        """
        Decode the two reference lists in raw into a flattened dictionary.
        """
        half = ArrayHandler.get_byte_length(self, object_length)
        keys = ArrayHandler.decode_body(self, raw[:half], object_length)
        values = ArrayHandler.decode_body(self, raw[half:], object_length)
        return dict(zip(keys, values))

    def flatten(self, dictionary, objects):
        """Flatten a dictionary into a dictionary of references."""
        keys = ArrayHandler.flatten(self, dictionary.keys(), objects)
        values = ArrayHandler.flatten(self, dictionary.values(), objects)
        return dict(zip(keys, values))

    def unflatten(self, dictionary, objects):
        """Unflatten a dictionary into a dictionary of objects."""
        keys = ArrayHandler.unflatten(self, dictionary.keys(), objects)
        values = ArrayHandler.unflatten(self, dictionary.values(), objects)
        return dict(zip(keys, values))

    def collect_children(self, dictionary, objects):
        """Collect all the keys and values in dictionary."""
        ArrayHandler.collect_children(self, dictionary.keys(), objects)
        ArrayHandler.collect_children(self, dictionary.values(), objects)


class ObjectHandler(object):
    """A master handler class for all of the object handler classes."""

    def __init__(self):
        """Intialize one of every (useful) handler class."""
        handlers = [BooleanHandler(), IntegerHandler(), FloatHandler(),
                    DateHandler(), ByteArrayHander(), BytesHander(), StringHandler(),
                    UnicodeStringHandler(), ArrayHandler(self),
                    DictionaryHandler(self), UIDHandler()]
        self.size_handler = UIDHandler()
        self.size_handler.type_number = 1
        self.handlers_by_type_number = {}
        self.handlers_by_type = {}
        self.file_object = bytes()
        for handler in handlers:
            self.handlers_by_type_number.update({handler.type_number: handler})
            if type(handler.types) == type:
                self.handlers_by_type.update({handler.types: handler})
            else:
                for type_ in handler.types:
                    self.handlers_by_type.update({type_: handler})

    def set_reference_size(self, reference_size):
        """Set the reference size on the references handler."""
        array_handler = self.handlers_by_type[list]
        dict_handler = self.handlers_by_type[dict]
        array_handler.set_reference_size(reference_size)
        dict_handler.set_reference_size(reference_size)

    def encode(self, object_, handler=None):
        """Use the appropriate handler to encode the given object."""
        if handler is None:
            handler = self.handlers_by_type[type(object_)]
        object_length = handler.get_object_length(object_)
        first_byte = self.encode_first_byte(handler.type_number, object_length)
        body = handler.encode_body(object_, object_length)
        return first_byte + body

    def decode(self, file_object, handler=None):
        """Start reading in file_object, and decode the object found."""
        self.file_object = file_object
        object_type, object_length = self.decode_first_byte(self.file_object)
        if handler is None:
            handler = self.handlers_by_type_number[object_type]
        byte_length = handler.get_byte_length(object_length)
        raw = self.file_object[:byte_length]
        self.file_object = self.file_object[byte_length:]
        return handler.decode_body(raw, object_length)

    def flatten_objects(self, objects):
        """Flatten all objects in objects."""
        flattened_objects = {}
        for item_index, item in enumerate(objects):
            if type(item) in (list, dict):
                flattened = self.flatten(item, objects)
                flattened_objects.update({item_index: flattened})
        for index, object_ in flattened_objects.items():
            objects[index] = object_

    def flatten(self, object_, objects):
        """Flatten the given object, using the appropriate handler."""
        handler = self.handlers_by_type[type(object_)]
        return handler.flatten(object_, objects)

    def unflatten(self, object_, objects):
        """Unflatten the give object, using the appropriate handler."""
        if type(object_) in (list, dict):
            handler = self.handlers_by_type[type(object_)]
            return handler.unflatten(object_, objects)
        return object_

    def encode_first_byte(self, type_number, length):
        """
        Encode the first byte (or bytes if length is greater than 14) of a an
        encoded object. This encodes the type and length of the object.
        Boolean type objects never encode as more than one byte.
        """
        big = False
        if length >= 15 and type_number != 0:
            real_length = self.encode(length, handler=self.size_handler)
            length = 15
            big = True
        value = (type_number << 4) + length
        encoded = pack('B', value)
        if big:
            return encoded + real_length
        return encoded

    def decode_first_byte(self, file_object):
        """
        Get the type number and object length from the first byte of an object.
        Boolean type objects never encode as more than one byte.
        """
        c = file_object[0:1]
        self.file_object = file_object[1:]
        value = unpack('B', c)[0]
        object_type = value >> 4
        object_length = value & 0xF
        if object_length == 15 and object_type != 0:
            object_length = self.decode(self.file_object, handler=self.size_handler)
        return object_type, object_length

    def collect_objects(self, object_, objects):
        """
        Collect all the objects in object_ into objects, using the appropriate
        handler.
        """
        try:
            find_with_type(object_, objects)
        except ValueError:
            objects.append(object_)
            if type(object_) in (dict, list):
                handler = self.handlers_by_type[type(object_)]
                handler.collect_children(object_, objects)


class TableHandler(object):
    """A handler class for the offset table found in binary plists."""

    def __init__(self):
        self.formats = (None, 'B', 'H', 'BBB', 'L')
        self.endian = '>'

    def decode(self, file_object, offset_size, length, table_offset):
        """
        Decode the offset table in file_object. Returns a list of offsets.
        """
        file_object = file_object[table_offset:]
        offset_format = self.formats[offset_size]
        table_format = self.endian + offset_format * length
        raw = file_object[:offset_size * length]
        offsets = unpack(table_format, raw)
        if offset_size == 3:
            zip_args = [offsets[x::3] for x in range(3)]
            offsets = zip(*zip_args)
            offsets = [o[0] * 0x10000 + o[1] * 0x100 + o[2] for o in offsets]
        return offsets

    def encode(self, offsets, table_offset):
        """Return the encoded form of a list of offsets."""
        offset_size = get_byte_width(table_offset, 4)
        offset_format = self.formats[offset_size]
        table_format = self.endian + offset_format * len(offsets)
        if offset_size == 3:
            new_offsets = []
            for offset in offsets[:]:
                first = offset // 0x10000
                second = (offset % 0x10000) // 0x100
                third = (offset % 0x10000) % 0x100
                new_offsets += [first, second, third]
            offsets = new_offsets
        encoded = pack(table_format, *offsets)
        return encoded


class TrailerHandler(object):
    """A handler class for the 'trailer' found in binary plists."""

    def __init__(self):
        self.format = '>6xBB4xL4xL4xL'

    def decode(self, file_object):
        """Decode the final 32 bytes of file_object."""
        file_object = file_object[-32:]
        trailer = unpack(self.format, file_object)
        return trailer

    def encode(self, offsets, table_offset):
        """
        Encode the trailer for a binary plist file with given offsets and
        table_offet.
        """
        offset_size = get_byte_width(table_offset, 4)
        number_of_objects = len(offsets)
        reference_size = get_byte_width(number_of_objects, 2)
        root_object = 0
        return pack(self.format, offset_size, reference_size,
                    number_of_objects, root_object, table_offset)


def get_byte_width(value_to_store, max_byte_width):
    """
    Return the minimum number of bytes needed to store a given value as an
    unsigned integer. If the byte width needed exceeds max_byte_width, raise
    ValueError."""
    for byte_width in range(max_byte_width):
        if 0x100 ** byte_width <= value_to_store < 0x100 ** (byte_width + 1):
            return byte_width + 1
    raise ValueError


def find_with_type(value, list_):
    """
    Find value in list_, matching both for equality and type, and
    return the index it was found at. If not found, raise ValueError.
    """
    for index, comparison_value in enumerate(list_):
        if (type(value) == type(comparison_value) and
                value == comparison_value):
            return index
    raise ValueError


def flatten_object_list(object_list, objects):
    """Convert a list of objects to a list of references."""
    reference_list = []
    for object_ in object_list:
        reference = find_with_type(object_, objects)
        reference_list.append(reference)
    return reference_list


def unflatten_reference_list(references, objects, object_handler):
    """Convert a list of references to a list of objects."""
    object_list = []
    for reference in references:
        item = objects[reference]
        if isinstance(item, bytes):
            item = item.decode()
        item = object_handler.unflatten(item, objects)
        object_list.append(item)
    return object_list


def read(file_object):
    """
    Read a binary plist from an open file object that supports seeking.
    Return the root object.
    """
    trailer = read_trailer(file_object)
    offset_size, reference_size, length, root, table_offset = trailer
    offsets = read_table(file_object, offset_size, length, table_offset)
    root_object = read_objects(file_object, offsets, reference_size, root)
    return root_object


def read_trailer(file_object):
    """Read and return the final, "trailer", section of an open file object."""
    trailer_handler = TrailerHandler()
    trailer = trailer_handler.decode(file_object)
    return trailer


def read_table(file_object, offset_size, length, table_offset):
    """
    Read an offset table from an open file object and return the decoded
    offsets.
    """
    table_handler = TableHandler()
    offsets = table_handler.decode(file_object, offset_size,
                                   length, table_offset)
    return offsets


def read_objects(file_object, offsets, reference_size, root):
    """Read from an open file_object and return the decoded root object."""
    object_handler = ObjectHandler()
    object_handler.set_reference_size(reference_size)
    objects = []
    for offset in offsets:
        buf = file_object[offset:]
        object_ = object_handler.decode(buf)
        objects.append(object_)
    root_object = objects[root]
    return object_handler.unflatten(root_object, objects)


def generate(root_object):
    """
    return bplist buf
    """
    buf = b'bplist00'
    buf, offsets = write_objects(buf, root_object)
    buf, table_offset = write_table(buf, offsets)
    return write_trailer(buf, offsets, table_offset)


def write_objects(buf, root_object):
    """
    Flatten all objects, encode, and write the encoded objects to file_object.
    """
    objects = []
    object_handler = ObjectHandler()
    object_handler.collect_objects(root_object, objects)
    object_handler.flatten_objects(objects)
    reference_size = get_byte_width(len(objects), 2)
    object_handler.set_reference_size(reference_size)
    offsets = []
    for object_ in objects:
        offsets.append(len(buf))
        encoded_object = object_handler.encode(object_)
        buf += encoded_object
    return buf, offsets


def write_table(buf, offsets):
    """Encode the offsets and write to file_object."""
    table_handler = TableHandler()
    table_offset = len(buf)
    table = table_handler.encode(offsets, table_offset)
    buf += table
    return buf, table_offset


def write_trailer(buf, offsets, table_offset):
    """Encode the trailer section and write to file_object."""
    trailer_handler = TrailerHandler()
    trailer = trailer_handler.encode(offsets, table_offset)
    buf += trailer
    return buf


def load(fp, binary=None):
    if binary is None:
        if fp[:8] == b'bplist00':
            binary = True
        else:
            fp.seek(0)
            binary = False
    if binary is True:
        root_object = read(fp)
    elif binary is False:
        root_object = plistlib.loads(fp)
    return root_object


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
    'XCTCapabilities': XCTCapabilities

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

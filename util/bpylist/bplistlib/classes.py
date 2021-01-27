# encoding: utf-8
"""
This file contains classes that know how to handle various different parts of
a binary plist file.
"""

from datetime import datetime
from struct import pack, unpack
from time import mktime

from ._types import uid, Fill, FillType, unicode
from .functions import find_with_type, get_byte_width
from .functions import flatten_object_list, unflatten_reference_list


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
                    DateHandler(), ByteArrayHander(),BytesHander(),StringHandler(),
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

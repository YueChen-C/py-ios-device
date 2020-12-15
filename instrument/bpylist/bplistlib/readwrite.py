# encoding: utf-8
"""This file contains private read/write functions for the bplistlib module."""
import plistlib
import tempfile

from instrument.bpylist.bplistlib.classes import ObjectHandler, TableHandler
from instrument.bpylist.bplistlib.classes import TrailerHandler
from instrument.bpylist.bplistlib.functions import get_byte_width


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
            fp.seek(0)  # I'm not sure if this is necessary
            binary = False
    if binary is True:
        root_object = read(fp)
    elif binary is False:
        root_object = plistlib.readPlist(fp)
    return root_object


if __name__ == '__main__':
    # buf = b'bplist00\xd4\x01\x02\x03\x04\x05\x06\x07\nX$versionY$archiverT$topX$objects\x12\x00\x01\x86\xa0_\x10\x0fNSKeyedArchiver\xd1\x08\tTroot\x80\x01\xa2\x0b\x0cU$null_\x10#_requestChannelWithCode:identifier:\x08\x11\x1a$)27ILQSV\\\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x82'

    buf2= b'bplist00\xd4\x01\x02\x03\x04\x05\x06\x07\nX$versionY$archiverT$topX$objects\x12\x00\x01\x86\xa0_\x10\x0fNSKeyedArchiver\xd1\x08\tTroot\x80\x01\xa2\x0b\x0cU$null_\x10\x1f_notifyOfPublishedCapabilities:\x08\x11\x1a$)27ILQSV\\\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00~'
    # c = load(buf)
    # print(c)

    c2 = load(buf2)
    print(c2)
    # print(c.get('$version'))
    # buf = write(c)
    # print(buf)
    # c = load(buf)
    # print(c)

# encoding: utf-8
"""This file contains private functions for the bplistlib module."""


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

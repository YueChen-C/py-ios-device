# encoding: utf-8
"""This file contains private read/write functions for the bplistlib module."""
import plistlib

from util.bpylist.bplistlib.classes import ObjectHandler, TableHandler
from util.bpylist.bplistlib.classes import TrailerHandler
from util.bpylist.bplistlib.functions import get_byte_width


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


if __name__ == '__main__':
    # buf = b'bplist00\xd4\x01\x02\x03\x04\x05\x06\x07\nX$versionY$archiverT$topX$objects\x12\x00\x01\x86\xa0_\x10\x0fNSKeyedArchiver\xd1\x08\tTroot\x80\x01\xa2\x0b\x0cU$null_\x10#_requestChannelWithCode:identifier:\x08\x11\x1a$)27ILQSV\\\x00\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\r\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x82'

    buf2= b'bplist00\xd4\x01\x02\x03\x04\x05\x06|\x7fY$archiverX$objectsT$topX$version_\x10\x0fNSKeyedArchiver\xaf\x10\x14\x07\x08EKSTX[]8^_beikqruyU$null\xdf\x10"\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-./01121345633789:;<=>?@A113BC1DV$class_\x10\x1eaggregateStatisticsBeforeCrash_\x10\x17automationFrameworkPath_\x10\x18baselineFileRelativePath_\x10\x0fbaselineFileURL_\x10!defaultTestExecutionTimeAllowance_\x10\x19disablePerformanceMetricsZemitOSLogs]formatVersion_\x10\x1cgatherLocalizableStringsData_\x10\x16initializeForUITesting_\x10!maximumTestExecutionTimeAllowance_\x10\x11productModuleName_\x10\x1brandomExecutionOrderingSeed_\x10\x10reportActivities_\x10\x12reportResultsToIDE_\x10\x11sessionIdentifier_\x10\x18systemAttachmentLifetime_\x10\x1atargetApplicationArguments_\x10\x19targetApplicationBundleID_\x10\x1ctargetApplicationEnvironment_\x10\x15targetApplicationPath_\x10\x1btestApplicationDependencies_\x10\x1ctestApplicationUserOverrides_\x10\x16testBundleRelativePath]testBundleURL_\x10\x15testExecutionOrdering_\x10\x13testTimeoutsEnabled_\x10\x10testsDrivenByIDE_\x10\x18testsMustRunOnMainThreadZtestsToRun[testsToSkip_\x10\x1ftreatMissingBaselinesAsFailures_\x10\x16userAttachmentLifetime\x80\x02\x80\x03\x80\x08\x80\x00\x80\x00\x80\x00\x08\x80\t\t\x80\x00\x80\n\x80\x00\x80\x12\x10\x02\x80\x0b\x80\x00\x80\x00\x80\x00\x80\r\x80\x00\x80\x00\x80\x0f\x10\x00\x80\x00\x80\x00\x10\x01\xd2FGHIX$classesZ$classname\xa2IJ_\x10\x13XCTestConfigurationXNSObject\xd3\tLMNOQWNS.keysZNS.objects\x80\x07\xa1P\x80\x04\xa1R\x80\x05_\x10\x11XCSuiteRecordsKey\xd3\tLMUVW\x80\x06\xa0\xa0\xd2FGYZ\xa2ZJ\\NSDictionary\xd2FG\\Z\xa2ZJ_\x10C/Developer/Library/PrivateFrameworks/XCTAutomationSupport.framework_\x10\x14WebDriverAgentRunner\xd2\tM`a\x80\x0c\xa0\xd2FGcd\xa2dJWNSArray\xd3\tLMfgh\x80\x0e\xa0\xa0\xd2FGjZ\xa2ZJ\xd3\tlmnopWNS.base[NS.relative\x80\x11\x80\x00\x80\x10_\x10\x9afile:///private/var/containers/Bundle/Application/27EE0483-4045-468C-945D-0D409E1C4B47/WebDriverAgentRunner-Runner.app/PlugIns/WebDriverAgentRunner.xctest\xd2FGst\xa2tJUNSURL\xd2\tvwx\\NS.uuidbytes\x80\x13O\x10\x10\x95\x03\xe5\xd4\x82\xc7G7\xb6\x14-\x94DX\x82\xcb\xd2FGz{\xa2{JVNSUUID\xd1}~Troot\x80\x01\x12\x00\x01\x86\xa0\x00\x08\x00\x11\x00\x1b\x00$\x00)\x002\x00D\x00[\x00a\x00\xa8\x00\xaf\x00\xd0\x00\xea\x01\x05\x01\x17\x01;\x01W\x01b\x01p\x01\x8f\x01\xa8\x01\xcc\x01\xe0\x01\xfe\x02\x11\x02&\x02:\x02U\x02r\x02\x8e\x02\xad\x02\xc5\x02\xe3\x03\x02\x03\x1b\x03)\x03A\x03W\x03j\x03\x85\x03\x90\x03\x9c\x03\xbe\x03\xd7\x03\xd9\x03\xdb\x03\xdd\x03\xdf\x03\xe1\x03\xe3\x03\xe4\x03\xe6\x03\xe7\x03\xe9\x03\xeb\x03\xed\x03\xef\x03\xf1\x03\xf3\x03\xf5\x03\xf7\x03\xf9\x03\xfb\x03\xfd\x03\xff\x04\x01\x04\x03\x04\x05\x04\x07\x04\t\x04\x0e\x04\x17\x04"\x04%\x04;\x04D\x04K\x04S\x04^\x04`\x04b\x04d\x04f\x04h\x04|\x04\x83\x04\x85\x04\x86\x04\x87\x04\x8c\x04\x8f\x04\x9c\x04\xa1\x04\xa4\x04\xea\x05\x01\x05\x06\x05\x08\x05\t\x05\x0e\x05\x11\x05\x19\x05 \x05"\x05#\x05$\x05)\x05,\x053\x05;\x05G\x05I\x05K\x05M\x05\xea\x05\xef\x05\xf2\x05\xf8\x05\xfd\x06\n\x06\x0c\x06\x1f\x06$\x06\'\x06.\x061\x066\x068\x00\x00\x00\x00\x00\x00\x02\x01\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x06='    # c = load(buf)
    # print(c)

    c2 = load(buf2)
    print(c2)
    # print(c.get('$version'))
    # buf = write(c)
    # print(buf)
    # c = load(buf)
    # print(c)

# Referenced from
# https://opensource.apple.com/tarballs/xnu-7195.60.75/bsd/kern/kdebug.c
# https://gitee.com/mirrors/darwin-xnu/blob/main/bsd/kern/kdebug.c  kdebug.h


import enum
import io
import json
import struct

from construct import Struct, Const, Padding, Int32ul, Int64ul, Array, GreedyRange, Byte, FixedSized, \
    CString, GreedyBytes, this, Adapter, Int16ul, Switch, StreamError

from ios_device.util import plistlib
from ios_device.util.kc_data import kc_data_parse

# from pykdebugparser.kd_buf_parser import BplistAdapter

KDBG_CLASS_MASK = 0xff000000
KDBG_CLASS_OFFSET = 24
KDBG_CLASS_MAX = 0xff

KDBG_SUBCLASS_MASK = 0x00ff0000
KDBG_SUBCLASS_OFFSET = 16
KDBG_SUBCLASS_MAX = 0xff

# ## /* class and subclass mask */
KDBG_CSC_MASK = 0xffff0000
KDBG_CSC_OFFSET = KDBG_SUBCLASS_OFFSET
KDBG_CSC_MAX = 0xffff

KDBG_CODE_MASK = 0x0000fffc
KDBG_CODE_OFFSET = 2
KDBG_CODE_MAX = 0x3fff

KDBG_EVENTID_MASK = 0xfffffffc
KDBG_FUNC_MASK = 0x00000003
VERSION2_FLAG = b'\x00\x02\xaa\x55'
VERSION3_FLAG = b'\x00\x03\xaa\x55'
KD_BUF_FORMAT = '<Q32sQLLQ'


def kdbg_extract_class(Debugid):
    return (Debugid & KDBG_CLASS_MASK) >> KDBG_CLASS_OFFSET


def kdbg_extract_subclass(Debugid):
    return (Debugid & KDBG_SUBCLASS_MASK) >> KDBG_SUBCLASS_OFFSET


def kdbg_extract_csc(Debugid):
    return (Debugid & KDBG_CSC_MASK) >> KDBG_CSC_OFFSET


def kdbg_extract_code(Debugid):
    return (Debugid & KDBG_CODE_MASK) >> KDBG_CODE_OFFSET


def kdbg_extract_all(Debugid):
    class_extracted = (Debugid & KDBG_CLASS_MASK) >> KDBG_CLASS_OFFSET
    subclass_extracted = (Debugid & KDBG_SUBCLASS_MASK) >> KDBG_SUBCLASS_OFFSET
    code_extracted = (Debugid & KDBG_CODE_MASK) >> KDBG_CODE_OFFSET
    return class_extracted, subclass_extracted, code_extracted


class DgbFuncQual(enum.Enum):
    """
    ## /* function qualifiers  */
        DBG_FUNC_START 1U
        DBG_FUNC_END   2U
        DBG_FUNC_NONE = 0U
    Event's role in the trace.
    """
    DBG_FUNC_NONE = 0
    DBG_FUNC_START = 1
    DBG_FUNC_END = 2
    DBG_FUNC_ALL = 3


class DebugClasses(enum.Enum):
    DBG_MACH = 1
    DBG_NETWORK = 2
    DBG_FSYSTEM = 3
    DBG_BSD = 4
    DBG_IOKIT = 5
    DBG_DRIVERS = 6
    DBG_TRACE = 7
    DBG_DLIL = 8
    DBG_PTHREAD = 9
    DBG_CORESTORAGE = 10
    DBG_CG = 11
    DBG_MONOTONIC = 12
    DBG_MISC = 20
    DBG_SECURITY = 30
    DBG_DYLD = 31
    DBG_QT = 32
    DBG_APPS = 33
    DBG_LAUNCHD = 34
    DBG_SILICON = 35
    DBG_PERF = 37
    DBG_IMPORTANCE = 38
    DBG_BANK = 40
    DBG_XPC = 41
    DBG_ATM = 42
    DBG_ARIADNE = 43
    DBG_DAEMON = 44
    DBG_ENERGYTRACE = 45
    DBG_DISPATCH = 46
    DBG_IMG = 49
    DBG_UMALLOC = 51
    DBG_TURNSTILE = 53
    DBG_MIG = 255


class DBG_MACH(enum.Enum):
    DBG_MACH_EXCP_KTRAP_x86 = 0x02  ## /* Kernel Traps on x86 */
    DBG_MACH_EXCP_DFLT = 0x03  ## /* deprecated name */
    DBG_MACH_EXCP_SYNC_ARM = 0x03  ## /* arm/arm64 synchronous exception */
    DBG_MACH_EXCP_IFLT = 0x04  ## /* deprecated name */
    DBG_MACH_EXCP_SERR_ARM = 0x04  ## /* arm/arm64 SError (async) exception */
    DBG_MACH_EXCP_INTR = 0x05  ## /* Interrupts */
    DBG_MACH_EXCP_ALNG = 0x06  ## /* Alignment Exception */
    DBG_MACH_EXCP_UTRAP_x86 = 0x07  ## /* User Traps on x86 */
    DBG_MACH_EXCP_FP = 0x08  ## /* FP Unavail */
    DBG_MACH_EXCP_DECI = 0x09  ## /* Decrementer Interrupt */
    DBG_MACH_CHUD = 0x0A  ## /* deprecated name */
    DBG_MACH_SIGNPOST = 0x0A  ## /* kernel signposts */
    DBG_MACH_EXCP_SC = 0x0C  ## /* System Calls */
    DBG_MACH_EXCP_TRACE = 0x0D  ## /* Trace exception */
    DBG_MACH_EXCP_EMUL = 0x0E  ## /* Instruction emulated */
    DBG_MACH_IHDLR = 0x10  ## /* Interrupt Handlers */
    DBG_MACH_IPC = 0x20  ## /* Inter Process Comm */
    DBG_MACH_RESOURCE = 0x25  ## /* tracing limits, etc */
    DBG_MACH_VM = 0x30  ## /* Virtual Memory */
    DBG_MACH_LEAKS = 0x31  ## /* alloc/free */
    DBG_MACH_WORKINGSET = 0x32  ## /* private subclass for working set related debugging */
    DBG_MACH_SCHED = 0x40  ## /* Scheduler */
    DBG_MACH_MSGID_INVALID = 0x50  ## /* Messages - invalid */
    DBG_MACH_LOCKS = 0x60  ## /* new lock APIs */
    DBG_MACH_PMAP = 0x70  ## /* pmap */
    DBG_MACH_CLOCK = 0x80  ## /* clock */
    DBG_MACH_MP = 0x90  ## /* MP related */
    DBG_MACH_VM_PRESSURE = 0xA0  ## /* Memory Pressure Events */
    DBG_MACH_STACKSHOT = 0xA1  ## /* Stackshot/Microstackshot subsystem */
    DBG_MACH_SFI = 0xA2  ## /* Selective Forced Idle (SFI) */
    DBG_MACH_ENERGY_PERF = 0xA3  ## /* Energy/performance resource stats */
    DBG_MACH_SYSDIAGNOSE = 0xA4  ## /* sysdiagnose */
    DBG_MACH_ZALLOC = 0xA5  ## /* Zone allocator */
    DBG_MACH_THREAD_GROUP = 0xA6  ## /* Thread groups */
    DBG_MACH_COALITION = 0xA7  ## /* Coalitions */
    DBG_MACH_SHAREDREGION = 0xA8  ## /* Shared region */
    DBG_MACH_SCHED_CLUTCH = 0xA9  ## /* Clutch scheduler */
    DBG_MACH_IO = 0xAA  ## /* I/O */
    DBG_MACH_WORKGROUP = 0xAB  ## /* Workgroup subsystem */


class DBG_MACH_IO(enum.Enum):
    DBC_MACH_IO_MMIO_READ = 0x1
    DBC_MACH_IO_MMIO_WRITE = 0x2
    DBC_MACH_IO_PHYS_READ = 0x3
    DBC_MACH_IO_PHYS_WRITE = 0x4
    DBC_MACH_IO_PORTIO_READ = 0x5
    DBC_MACH_IO_PORTIO_WRITE = 0x6


class DBG_MACH_EXCP_INTR(enum.Enum):
    DBG_INTR_TYPE_UNKNOWN = 0x0  ## /* default/unknown interrupt */
    DBG_INTR_TYPE_IPI = 0x1  ## /* interprocessor interrupt */
    DBG_INTR_TYPE_TIMER = 0x2  ## /* timer interrupt */
    DBG_INTR_TYPE_OTHER = 0x3  ## /* other (usually external) interrupt */
    DBG_INTR_TYPE_PMI = 0x4  ## /* performance monitor interrupt */


class DBG_MACH_SCHED(enum.Enum):
    MACH_SCHED = 0x0  # /* Scheduler */
    MACH_STACK_ATTACH = 0x1  # /* stack_attach() */
    MACH_STACK_HANDOFF = 0x2  # /* stack_handoff() */
    MACH_CALL_CONT = 0x3  # /* call_continuation() */
    MACH_CALLOUT = 0x4  # /* callouts */
    MACH_STACK_DETACH = 0x5
    MACH_MAKE_RUNNABLE = 0x6  # /* make thread runnable */
    MACH_PROMOTE = 0x7  # /* promoted due to resource (replaced by MACH_PROMOTED) */
    MACH_DEMOTE = 0x8  # /* promotion undone (replaced by MACH_UNPROMOTED) */
    MACH_IDLE = 0x9  # /* processor idling */
    MACH_STACK_DEPTH = 0xa  # /* stack depth at switch */
    MACH_MOVED = 0xb  # /* did not use original scheduling decision */
    MACH_PSET_LOAD_AVERAGE = 0xc
    MACH_AMP_DEBUG = 0xd
    MACH_FAILSAFE = 0xe  # /* tripped fixed-pri/RT failsafe */
    MACH_BLOCK = 0xf  # /* thread block */
    MACH_WAIT = 0x10  # /* thread wait assertion */
    MACH_GET_URGENCY = 0x14  # /* Urgency queried by platform */
    MACH_URGENCY = 0x15  # /* Urgency (RT/BG/NORMAL) communicated
    MACH_REDISPATCH = 0x16  # /* "next thread" thread redispatched */
    MACH_REMOTE_AST = 0x17  # /* AST signal issued to remote processor */
    MACH_SCHED_CHOOSE_PROCESSOR = 0x18  # /* Result of choose_processor */
    MACH_DEEP_IDLE = 0x19  # /* deep idle on master processor */
    MACH_SCHED_DECAY_PRIORITY = 0x1a  # /*was MACH_SCHED_DECAY_PRIORITY */
    MACH_CPU_THROTTLE_DISABLE = 0x1b  # /* Global CPU Throttle Disable */
    MACH_RW_PROMOTE = 0x1c  # /* promoted due to RW lock promotion */
    MACH_RW_DEMOTE = 0x1d  # /* promotion due to RW lock undone */
    MACH_SCHED_MAINTENANCE = 0x1f  # /* periodic maintenance thread */
    MACH_DISPATCH = 0x20  # /* context switch completed */
    MACH_QUANTUM_HANDOFF = 0x21  # /* quantum handoff occurred */
    MACH_MULTIQ_DEQUEUE = 0x22  # /* Result of multiq dequeue */
    MACH_SCHED_THREAD_SWITCH = 0x23  # /* attempt direct context switch to hinted thread */
    MACH_SCHED_SMT_BALANCE = 0x24  # /* SMT load balancing ASTs */
    MACH_REMOTE_DEFERRED_AST = 0x25  # /* Deferred AST started against remote processor */
    MACH_REMOTE_CANCEL_AST = 0x26  # /* Canceled deferred AST for remote processor */
    MACH_SCHED_CHANGE_PRIORITY = 0x27  # /* thread sched priority changed */
    MACH_SCHED_UPDATE_REC_CORES = 0x28  # /* Change to recommended processor bitmask */
    MACH_STACK_WAIT = 0x29  # /* Thread could not be switched-to because of kernel stack shortage */
    MACH_THREAD_BIND = 0x2a  # /* Thread was bound (or unbound) to a processor */
    MACH_WAITQ_PROMOTE = 0x2b  # /* Thread promoted by waitq boost */
    MACH_WAITQ_DEMOTE = 0x2c  # /* Thread demoted from waitq boost */
    MACH_SCHED_LOAD = 0x2d  # /* load update */
    MACH_REC_CORES_FAILSAFE = 0x2e  # /* recommended processor failsafe kicked in */
    MACH_SCHED_QUANTUM_EXPIRED = 0x2f  # /* thread quantum expired */
    MACH_EXEC_PROMOTE = 0x30  # /* Thread promoted by exec boost */
    MACH_EXEC_DEMOTE = 0x31  # /* Thread demoted from exec boost */
    MACH_AMP_SIGNAL_SPILL = 0x32  # /* AMP spill signal sent to cpuid */
    MACH_AMP_STEAL = 0x33  # /* AMP thread stolen or spilled */
    MACH_SCHED_LOAD_EFFECTIVE = 0x34  # /* Effective scheduler load */
    MACH_PROMOTED = 0x35  # /* was: thread promoted due to mutex priority promotion */
    MACH_UNPROMOTED = 0x36  # /* was: thread unpromoted due to mutex priority promotion */
    MACH_PROMOTED_UPDATE = 0x37  # /* was: thread already promoted, but promotion priority changed */
    MACH_QUIESCENT_COUNTER = 0x38  # /* quiescent counter tick */
    MACH_TURNSTILE_USER_CHANGE = 0x39  # /* base priority change because of turnstile */
    MACH_AMP_RECOMMENDATION_CHANGE = 0x3a  # /* Thread group recommendation change */
    MACH_AMP_PERFCTL_POLICY_CHANGE = 0x3b  # /* AMP policy for perfctl cluster recommendation */
    MACH_TURNSTILE_KERNEL_CHANGE = 0x40  # /* sched priority change because of turnstile */
    MACH_SCHED_WI_AUTO_JOIN = 0x41  # /* work interval auto join events */
    MACH_SCHED_WI_DEFERRED_FINISH = 0x42  # /* work interval pending finish events for auto-join thread groups */
    MACH_PSET_AVG_EXEC_TIME = 0x50


class DBG_MACH_SCHED_CLUTCH(enum.Enum):
    MACH_SCHED_CLUTCH_ROOT_BUCKET_STATE = 0x0  # /* __unused */
    MACH_SCHED_CLUTCH_TG_BUCKET_STATE = 0x1  # /* __unused */
    MACH_SCHED_CLUTCH_THREAD_SELECT = 0x2  # /* Thread selection events for Clutch scheduler */
    MACH_SCHED_CLUTCH_THREAD_STATE = 0x3  # /* __unused */
    MACH_SCHED_CLUTCH_TG_BUCKET_PRI = 0x4  # /* Clutch bucket priority update event */
    MACH_SCHED_EDGE_CLUSTER_OVERLOAD = 0x5  # /* Cluster experienced overload; migrating threads to other clusters */
    MACH_SCHED_EDGE_STEAL = 0x6  # /* Per-cluster avg. thread execution time */
    MACH_SCHED_EDGE_REBAL_RUNNABLE = 0x7  # /* Rebalance runnable threads on a foreign cluster */
    MACH_SCHED_EDGE_REBAL_RUNNING = 0x8  # /* Rebalance running threads on a foreign cluster */
    MACH_SCHED_EDGE_SHOULD_YIELD = 0x9  # /* Edge decisions for thread yield */
    MACH_SCHED_CLUTCH_THR_COUNT = 0xa  # /* Clutch scheduler runnable thread counts */
    MACH_SCHED_EDGE_LOAD_AVG = 0xb  # /* Per-cluster load average */


class DBG_MACH_WORKGROUP(enum.Enum):
    WORKGROUP_INTERVAL_CREATE = 0x0  # /* work interval creation */
    WORKGROUP_INTERVAL_DESTROY = 0x1  # /* work interval destruction */
    WORKGROUP_INTERVAL_CHANGE = 0x2  # /* thread work interval change */
    WORKGROUP_INTERVAL_START = 0x3  # /* work interval start call */
    WORKGROUP_INTERVAL_UPDATE = 0x4  # /* work interval update call */
    WORKGROUP_INTERVAL_FINISH = 0x5  # /* work interval finish call */


class DBG_MACH_IPC(enum.Enum):
    MACH_TASK_SUSPEND = 0x0  # /* Suspended a task */
    MACH_TASK_RESUME = 0x1  # /* Resumed a task */
    MACH_THREAD_SET_VOUCHER = 0x2
    MACH_IPC_MSG_SEND = 0x3  # /* mach msg send, uniq msg info */
    MACH_IPC_MSG_RECV = 0x4  # /* mach_msg receive */
    MACH_IPC_MSG_RECV_VOUCHER_REFUSED = 0x5  # /* mach_msg receive, voucher refused */
    MACH_IPC_KMSG_FREE = 0x6  # /* kernel free of kmsg data */
    MACH_IPC_VOUCHER_CREATE = 0x7  # /* Voucher added to global voucher hashtable */
    MACH_IPC_VOUCHER_CREATE_ATTR_DATA = 0x8  # /* Attr data for newly created voucher */
    MACH_IPC_VOUCHER_DESTROY = 0x9  # /* Voucher removed from global voucher hashtable */
    MACH_IPC_KMSG_INFO = 0xa  # /* Send/Receive info for a kmsg */
    MACH_IPC_KMSG_LINK = 0xb  # /* link a kernel kmsg pointer to user mach_msg_header_t */
    MACH_IPC_PORT_ENTRY_MODIFY = 0xc  # /* A port space gained or lost a port right (reference) */
    MACH_IPC_DESTROY_GUARDED_DESC = 0xd  # /* Unable to receive a guarded descriptor */


class DBG_MACH_THREAD_GROUP(enum.Enum):
    MACH_THREAD_GROUP_NEW = 0x0
    MACH_THREAD_GROUP_FREE = 0x1
    MACH_THREAD_GROUP_SET = 0x2
    MACH_THREAD_GROUP_NAME = 0x3
    MACH_THREAD_GROUP_NAME_FREE = 0x4
    MACH_THREAD_GROUP_FLAGS = 0x5
    MACH_THREAD_GROUP_BLOCK = 0x6


class DBG_MACH_COALITION(enum.Enum):
    MACH_COALITION_NEW = 0x0
    MACH_COALITION_FREE = 0x1
    MACH_COALITION_ADOPT = 0x2
    MACH_COALITION_REMOVE = 0x3
    MACH_COALITION_THREAD_GROUP_SET = 0x4


class DBG_MACH_PMAP(enum.Enum):
    MACH_COALITION_NEW = 0x0
    MACH_COALITION_FREE = 0x1
    MACH_COALITION_ADOPT = 0x2
    MACH_COALITION_REMOVE = 0x3
    MACH_COALITION_THREAD_GROUP_SET = 0x4


class DBG_MACH_CLOCK(enum.Enum):
    MACH_EPOCH_CHANGE = 0x0  # /* wake epoch change */
    MACH_BRIDGE_RCV_TS = 0x1  # /* receive timestamp pair from interrupt handler */
    MACH_BRIDGE_REMOTE_TIME = 0x2  # /* calculate remote timestamp */
    MACH_BRIDGE_RESET_TS = 0x3  # /* reset timestamp conversion parameters */
    MACH_BRIDGE_TS_PARAMS = 0x4  # /* recompute timestamp conversion parameters */
    MACH_BRIDGE_SKIP_TS = 0x5  # /* skip timestamp */
    MACH_BRIDGE_TS_MISMATCH = 0x6  # /* mismatch between predicted and received remote timestamp */
    MACH_BRIDGE_OBSV_RATE = 0x7  # /* out of range observed rates */


class DBG_MACH_STACKSHOT(enum.Enum):
    MICROSTACKSHOT_RECORD = 0x0
    MICROSTACKSHOT_GATHER = 0x1


class DBG_MACH_SYSDIAGNOSE(enum.Enum):
    SYSDIAGNOSE_NOTIFY_USER = 0x0
    SYSDIAGNOSE_FULL = 0x1
    SYSDIAGNOSE_STACKSHOT = 0x2
    SYSDIAGNOSE_TAILSPIN = 0x3


class DBG_MACH_SFI(enum.Enum):
    SFI_SET_WINDOW = 0x0
    SFI_CANCEL_WINDOW = 0x1
    SFI_SET_CLASS_OFFTIME = 0x2
    SFI_CANCEL_CLASS_OFFTIME = 0x3
    SFI_THREAD_DEFER = 0x4
    SFI_OFF_TIMER = 0x5
    SFI_ON_TIMER = 0x6
    SFI_WAIT_CANCELED = 0x7
    SFI_PID_SET_MANAGED = 0x8
    SFI_PID_CLEAR_MANAGED = 0x9
    SFI_GLOBAL_DEFER = 0xa


class DBG_MACH_ZALLOC(enum.Enum):
    ZALLOC_ZCRAM = 0x0


class DBG_MACH_RESOURCE(enum.Enum):
    RMON_ENABLE_CPUUSAGE_MONITOR = 0x001
    RMON_CPUUSAGE_VIOLATED = 0x002
    RMON_CPUUSAGE_SUSPENDED = 0x003
    RMON_CPUUSAGE_VIOLATED_K32A = 0x004
    RMON_CPUUSAGE_VIOLATED_K32B = 0x005
    RMON_CPUUSAGE_RESUMED = 0x006
    RMON_DISABLE_CPUUSAGE_MONITOR = 0x00f

    RMON_ENABLE_CPUWAKES_MONITOR = 0x011
    RMON_CPUWAKES_VIOLATED = 0x012
    RMON_CPUWAKES_VIOLATED_K32A = 0x014
    RMON_CPUWAKES_VIOLATED_K32B = 0x015
    RMON_DISABLE_CPUWAKES_MONITOR = 0x01f

    RMON_ENABLE_IO_MONITOR = 0x021
    RMON_LOGWRITES_VIOLATED = 0x022
    RMON_PHYSWRITES_VIOLATED = 0x023
    RMON_LOGWRITES_VIOLATED_K32A = 0x024
    RMON_LOGWRITES_VIOLATED_K32B = 0x025
    RMON_DISABLE_IO_MONITOR = 0x02f


class DBG_NETWORK(enum.Enum):
    DBG_NETIP = 1  # /* Internet Protocol */
    DBG_NETARP = 2  # /* Address Resolution Protocol */
    DBG_NETUDP = 3  # /* User Datagram Protocol */
    DBG_NETTCP = 4  # /* Transmission Control Protocol */
    DBG_NETICMP = 5  # /* Internet Control Message Protocol */
    DBG_NETIGMP = 6  # /* Internet Group Management Protocol */
    DBG_NETRIP = 7  # /* Routing Information Protocol */
    DBG_NETOSPF = 8  # /* Open Shortest Path First */
    DBG_NETISIS = 9  # /* Intermediate System to Intermediate System */
    DBG_NETSNMP = 10  # /* Simple Network Management Protocol */
    DBG_NETSOCK = 11  # /* Socket Layer */
    DBG_NETAARP = 100  # /* Apple ARP */
    DBG_NETDDP = 101  # /* Datagram Delivery Protocol */
    DBG_NETNBP = 102  # /* Name Binding Protocol */
    DBG_NETZIP = 103  # /* Zone Information Protocol */
    DBG_NETADSP = 104  # /* Name Binding Protocol */
    DBG_NETATP = 105  # /* Apple Transaction Protocol */
    DBG_NETASP = 106  # /* Apple Session Protocol */
    DBG_NETAFP = 107  # /* Apple Filing Protocol */
    DBG_NETRTMP = 108  # /* Routing Table Maintenance Protocol */
    DBG_NETAURP = 109  # /* Apple Update Routing Protocol */

    DBG_NETIPSEC = 128  # /* IPsec Protocol  */
    DBG_NETVMNET = 129  # /* VMNet */


class DBG_IOKIT(enum.Enum):
    DBG_IOINTC = 0  # /* Interrupt controller */
    DBG_IOWORKLOOP = 1  # /* Work from work loop */
    DBG_IOINTES = 2  # /* Interrupt event source */
    DBG_IOCLKES = 3  # /* Clock event source */
    DBG_IOCMDQ = 4  # /* Command queue latencies */
    DBG_IOMCURS = 5  # /* Memory Cursor */
    DBG_IOMDESC = 6  # /* Memory Descriptors */
    DBG_IOPOWER = 7  # /* Power Managerment */
    DBG_IOSERVICE = 8  # /* Matching etc. */
    DBG_IOREGISTRY = 9  # /* Registry */

    # **** 9-32 reserved for internal IOKit usage ****

    DBG_IOSTORAGE = 32  # /* Storage layers */
    DBG_IONETWORK = 33  # /* Network layers */
    DBG_IOKEYBOARD = 34  # /* Keyboard */
    DBG_IOHID = 35  # /* HID Devices */
    DBG_IOAUDIO = 36  # /* Audio */
    DBG_IOSERIAL = 37  # /* Serial */
    DBG_IOTTY = 38  # /* TTY layers */
    DBG_IOSAM = 39  # /* SCSI Architecture Model layers */
    DBG_IOPARALLELATA = 40  # /* Parallel ATA */
    DBG_IOPARALLELSCSI = 41  # /* Parallel SCSI */
    DBG_IOSATA = 42  # /* Serial-ATA */
    DBG_IOSAS = 43  # /* SAS */
    DBG_IOFIBRECHANNEL = 44  # /* FiberChannel */
    DBG_IOUSB = 45  # /* USB */
    DBG_IOBLUETOOTH = 46  # /* Bluetooth */
    DBG_IOFIREWIRE = 47  # /* FireWire */
    DBG_IOINFINIBAND = 48  # /* Infiniband */
    DBG_IOCPUPM = 49  # /* CPU Power Management */
    DBG_IOGRAPHICS = 50  # /* Graphics */
    DBG_HIBERNATE = 51  # /* hibernation related events */
    DBG_IOTHUNDERBOLT = 52  # /* Thunderbolt */
    DBG_BOOTER = 53  # /* booter related events */
    DBG_IOAUDIO2 = 54  # /* Audio (extended) */

    DBG_IOSURFACEPA = 64  # /* IOSurface page mappings */
    DBG_IOMDPA = 65  # /* IOMemoryDescriptor page mappings */
    DBG_IODARTPA = 66  # /* DART page mappings */


class DBG_DRIVERS(enum.Enum):
    DBG_DRVSTORAGE = 1  # /* Storage layers */
    DBG_DRVNETWORK = 2  # /* Network layers */
    DBG_DRVKEYBOARD = 3  # /* Keyboard */
    DBG_DRVHID = 4  # /* HID Devices */
    DBG_DRVAUDIO = 5  # /* Audio */
    DBG_DRVSERIAL = 7  # /* Serial */
    DBG_DRVSAM = 8  # /* SCSI Architecture Model layers */
    DBG_DRVPARALLELATA = 9  # /* Parallel ATA */
    DBG_DRVPARALLELSCSI = 10  # /* Parallel SCSI */
    DBG_DRVSATA = 11  # /* Serial ATA */
    DBG_DRVSAS = 12  # /* SAS */
    DBG_DRVFIBRECHANNEL = 13  # /* FiberChannel */
    DBG_DRVUSB = 14  # /* USB */
    DBG_DRVBLUETOOTH = 15  # /* Bluetooth */
    DBG_DRVFIREWIRE = 16  # /* FireWire */
    DBG_DRVINFINIBAND = 17  # /* Infiniband */
    DBG_DRVGRAPHICS = 18  # /* Graphics */
    DBG_DRVSD = 19  # /* Secure Digital */
    DBG_DRVNAND = 20  # /* NAND drivers and layers */
    DBG_SSD = 21  # /* SSD */
    DBG_DRVSPI = 22  # /* SPI */
    DBG_DRVWLAN_802_11 = 23  # /* WLAN 802.11 */
    DBG_DRVSSM = 24  # /* System State Manager(AppleSSM) */
    DBG_DRVSMC = 25  # /* System Management Controller */
    DBG_DRVMACEFIMANAGER = 26  # /* Mac EFI Manager */
    DBG_DRVANE = 27  # /* ANE */
    DBG_DRVETHERNET = 28  # /* Ethernet */
    DBG_DRVMCC = 29  # /* Memory Cache Controller */
    DBG_DRVACCESSORY = 30  # /* Accessories */


class DBG_DLIL(enum.Enum):
    DBG_DLIL_STATIC = 1  # /* Static DLIL code */
    DBG_DLIL_PR_MOD = 2  # /* DLIL Protocol Module */
    DBG_DLIL_IF_MOD = 3  # /* DLIL Interface Module */
    DBG_DLIL_PR_FLT = 4  # /* DLIL Protocol Filter */
    DBG_DLIL_IF_FLT = 5  # /* DLIL Interface FIlter */


class DBG_FSYSTEM(enum.Enum):
    DBG_FSRW = 0x1  # /* reads and writes to the filesystem */
    DBG_DKRW = 0x2  # /* reads and writes to the disk */
    DBG_FSVN = 0x3  # /* vnode operations (inc. locking/unlocking) */
    DBG_FSLOOOKUP = 0x4  # /* namei and other lookup-related operations */
    DBG_JOURNAL = 0x5  # /* journaling operations */
    DBG_IOCTL = 0x6  # /* ioctl to the disk */
    DBG_BOOTCACHE = 0x7  # /* bootcache operations */
    DBG_HFS = 0x8  # /* HFS-specific events; see the hfs project */
    DBG_APFS = 0x9  # /* APFS-specific events; see the apfs project */
    DBG_SMB = 0xA  # /* SMB-specific events; see the smb project */
    DBG_MOUNT = 0xB  # /* Mounting/unmounting operations */
    DBG_EXFAT = 0xE  # /* ExFAT-specific events; see the exfat project */
    DBG_MSDOS = 0xF  # /* FAT-specific events; see the msdosfs project */
    DBG_ACFS = 0x10  # /* Xsan-specific events; see the XsanFS project */
    DBG_THROTTLE = 0x11  # /* I/O Throttling events */
    DBG_DECMP = 0x12  # /* Decmpfs-specific events */
    DBG_VFS = 0x13  # /* VFS layer events */
    DBG_LIVEFS = 0x14  # /* LiveFS events; see the UserFS project */
    DBG_CONTENT_PROT = 0xCF  # /* Content Protection Events: see bsd/sys/cprotect.h */


class DBG_BSD(enum.Enum):
    DBG_BSD_PROC = 0x01  # /* process/signals related */
    DBG_BSD_MEMSTAT = 0x02  # /* memorystatus / jetsam operations */
    DBG_BSD_KEVENT = 0x03  # /* kqueue / kevent related */
    DBG_BSD_EXCP_SC = 0x0C  # /* System Calls */
    DBG_BSD_AIO = 0x0D  # /* aio (POSIX async IO) */
    DBG_BSD_SC_EXTENDED_INFO = 0x0E  # /* System Calls, extended info */
    DBG_BSD_SC_EXTENDED_INFO2 = 0x0F  # /* System Calls, extended info */
    DBG_BSD_KDEBUG_TEST = 0xFF  # /* for testing kdebug */


class DBG_BSD_PROC(enum.Enum):
    BSD_PROC_EXIT = 1  # /* process exit */
    BSD_PROC_FRCEXIT = 2  # /* Kernel force termination */
    BSD_PROC_EXEC = 3  # /* process spawn / exec */
    BSD_PROC_EXITREASON_CREATE = 4  # /* exit reason creation */
    BSD_PROC_EXITREASON_COMMIT = 5  # /* exit reason commited to a proc */


class DBG_BSD_MEMSTAT(enum.Enum):
    BSD_MEMSTAT_SCAN = 1  # /* memorystatus thread awake */
    BSD_MEMSTAT_JETSAM = 2  # /* LRU jetsam */
    BSD_MEMSTAT_JETSAM_HIWAT = 3  # /* highwater jetsam */
    BSD_MEMSTAT_FREEZE = 4  # /* freeze process */
    BSD_MEMSTAT_FREEZE_SCAN = 5  # /* select a process to freeze and freeze it */
    BSD_MEMSTAT_UPDATE = 6  # /* priority update */
    BSD_MEMSTAT_IDLE_DEMOTE = 7  # /* idle demotion fired */
    BSD_MEMSTAT_CLEAR_ERRORS = 8  # /* reset termination error state */
    BSD_MEMSTAT_DIRTY_TRACK = 9  # /* track the process state */
    BSD_MEMSTAT_DIRTY_SET = 10  # /* set the process state */
    BSD_MEMSTAT_DIRTY_CLEAR = 11  # /* clear the process state */
    BSD_MEMSTAT_GRP_SET_PROP = 12  # /* set group properties */
    BSD_MEMSTAT_DO_KILL = 13  # /* memorystatus kills */
    BSD_MEMSTAT_CHANGE_PRIORITY = 14  # /* priority changed */
    BSD_MEMSTAT_FAST_JETSAM = 15  # /* Aggressive jetsam ("clear-the-deck") */
    BSD_MEMSTAT_COMPACTOR_RUN = 16  # /* run VM compactor after process kill */
    BSD_MEMSTAT_FREEZE_DISABLE = 17  # /* disable freeze and kill frozen processes */
    BSD_MEMSTAT_RELAUNCH_FLAGS = 18  # /* flags representing jetsam behavior; based on launchd data */


class DBG_BSD_KEVENT(enum.Enum):
    BSD_KEVENT_KQ_PROCESS_BEGIN = 1
    BSD_KEVENT_KQ_PROCESS_END = 2
    BSD_KEVENT_KQWQ_PROCESS_BEGIN = 3
    BSD_KEVENT_KQWQ_PROCESS_END = 4
    BSD_KEVENT_KQWQ_BIND = 5
    BSD_KEVENT_KQWQ_UNBIND = 6
    BSD_KEVENT_KQWQ_THREQUEST = 7
    BSD_KEVENT_KQWL_PROCESS_BEGIN = 8
    BSD_KEVENT_KQWL_PROCESS_END = 9
    BSD_KEVENT_KQWL_THREQUEST = 10
    BSD_KEVENT_KQWL_THADJUST = 11
    BSD_KEVENT_KQ_REGISTER = 12
    BSD_KEVENT_KQWQ_REGISTER = 13
    BSD_KEVENT_KQWL_REGISTER = 14
    BSD_KEVENT_KNOTE_ACTIVATE = 15
    BSD_KEVENT_KQ_PROCESS = 16
    BSD_KEVENT_KQWQ_PROCESS = 17
    BSD_KEVENT_KQWL_PROCESS = 18
    BSD_KEVENT_KQWL_BIND = 19
    BSD_KEVENT_KQWL_UNBIND = 20
    BSD_KEVENT_KNOTE_ENABLE = 21
    BSD_KEVENT_KNOTE_VANISHED = 22


class DBG_TRACE(enum.Enum):
    DBG_TRACE_DATA = 0
    DBG_TRACE_STRING = 1
    DBG_TRACE_INFO = 2


class DBG_CORESTORAGE(enum.Enum):
    DBG_CS_IO = 0


class DBG_SECURITY(enum.Enum):
    DBG_SEC_KERNEL = 0  # /* raw entropy collected by the kernel */
    DBG_SEC_SANDBOX = 1


class DBG_MONOTONIC(enum.Enum):
    DBG_MT_INSTRS_CYCLES = 1
    DBG_MT_DEBUG = 2
    DBG_MT_RESOURCES_PROC_EXIT = 3
    DBG_MT_RESOURCES_THR_EXIT = 4
    DBG_MT_TMPTH = 0xfe
    DBG_MT_TMPCPU = 0xff


class DBG_MISC(enum.Enum):
    DBG_MISC_COREBRIGHTNESS = 0x01
    DBG_MISC_VIDEOENG = 0x02
    DBG_EVENT = 0x10
    DBG_MISC_INSTRUMENTS = 0x11
    DBG_MISC_INSTRUMENTSBT = 0x12
    DBG_MISC_LAYOUT = 0x1a
    DBG_BUFFER = 0x20


class DBG_DYLD(enum.Enum):
    DBG_DYLD_UUID = 5


class DBG_DYLD_UUID(enum.Enum):
    DBG_DYLD_UUID_MAP_A = (0)
    DBG_DYLD_UUID_MAP_B = (1)
    DBG_DYLD_UUID_MAP_32_A = (2)
    DBG_DYLD_UUID_MAP_32_B = (3)
    DBG_DYLD_UUID_MAP_32_C = (4)
    DBG_DYLD_UUID_UNMAP_A = (5)
    DBG_DYLD_UUID_UNMAP_B = (6)
    DBG_DYLD_UUID_UNMAP_32_A = (7)
    DBG_DYLD_UUID_UNMAP_32_B = (8)
    DBG_DYLD_UUID_UNMAP_32_C = (9)
    DBG_DYLD_UUID_SHARED_CACHE_A = (10)
    DBG_DYLD_UUID_SHARED_CACHE_B = (11)
    DBG_DYLD_UUID_SHARED_CACHE_32_A = (12)
    DBG_DYLD_UUID_SHARED_CACHE_32_B = (13)
    DBG_DYLD_UUID_SHARED_CACHE_32_C = (14)
    DBG_DYLD_AOT_UUID_MAP_A = (15)
    DBG_DYLD_AOT_UUID_MAP_B = (16)


class DBG_DKRW(enum.Enum):
    DKIO_DONE = 0x01
    DKIO_READ = 0x02
    DKIO_ASYNC = 0x04
    DKIO_META = 0x08
    DKIO_PAGING = 0x10
    DKIO_THROTTLE = 0x20  # /* Deprecated, still provided so fs_usage doesn't break */
    DKIO_PASSIVE = 0x40
    DKIO_NOCACHE = 0x80
    DKIO_TIER_MASK = 0xF00
    DKIO_TIER_SHIFT = 8
    DKIO_TIER_UPGRADE = 0x1000


class DBG_APPS(enum.Enum):
    DBG_APP_LOGINWINDOW = 0x03
    DBG_APP_AUDIO = 0x04
    DBG_APP_SYSTEMUI = 0x05
    DBG_APP_SIGNPOST = 0x0A
    DBG_APP_APPKIT = 0x0C
    DBG_APP_UIKIT = 0x0D
    DBG_APP_DFR = 0x0E
    DBG_APP_LAYOUT = 0x0F
    DBG_APP_COREDATA = 0x10
    DBG_APP_SAMBA = 0x80
    DBG_APP_EOSSUPPORT = 0x81
    DBG_APP_MACEFIMANAGER = 0x82


class DBG_THROTTLE(enum.Enum):
    OPEN_THROTTLE_WINDOW = 0x1
    PROCESS_THROTTLED = 0x2
    IO_THROTTLE_DISABLE = 0x3
    IO_TIER_UPL_MISMATCH = 0x4


class DBG_PERF(enum.Enum):
    PERF_EVENT = 0
    PERF_DATA = 1
    PERF_STK = 2


class DBG_IMPORTANCE(enum.Enum):
    IMP_ASSERTION = 0x10  # /* Task takes/drops a boost assertion */
    IMP_BOOST = 0x11  # /* Task boost level changed */
    IMP_MSG = 0x12  # /* boosting message sent by donating task on donating port */
    IMP_WATCHPORT = 0x13  # /* port marked as watchport, and boost was transferred to the watched task */
    IMP_TASK_SUPPRESSION = 0x17  # /* Task changed suppression behaviors */
    IMP_TASK_APPTYPE = 0x18  # /* Task launched with apptype */
    IMP_UPDATE = 0x19  # /* Requested -> effective calculation */
    IMP_USYNCH_QOS_OVERRIDE = 0x1A  # /* Userspace synchronization applied QoS override to resource owning thread */
    IMP_DONOR_CHANGE = 0x1B  # /* The iit_donor bit changed */
    IMP_MAIN_THREAD_QOS = 0x1C  # /* The task's main thread QoS was set */
    IMP_SYNC_IPC_QOS = 0x1D  # /* Sync IPC QOS override */
    IMP_TASK_POLICY_DARWIN_BG = 0x21
    IMP_TASK_POLICY_IOPOL = 0x22
    IMP_TASK_POLICY_IO = 0x23
    IMP_TASK_POLICY_PASSIVE_IO = 0x24
    IMP_TASK_POLICY_DARWIN_BG_IOPOL = 0x27
    IMP_TASK_POLICY_TAL = 0x28
    IMP_TASK_POLICY_BOOST = 0x29
    IMP_TASK_POLICY_ROLE = 0x2A
    IMP_TASK_POLICY_TERMINATED = 0x2C
    IMP_TASK_POLICY_NEW_SOCKETS_BG = 0x2D
    IMP_TASK_POLICY_SUP_ACTIVE = 0x2E
    IMP_TASK_POLICY_LATENCY_QOS = 0x2F
    IMP_TASK_POLICY_THROUGH_QOS = 0x30
    IMP_TASK_POLICY_WATCHERS_BG = 0x31
    IMP_TASK_POLICY_SFI_MANAGED = 0x34
    IMP_TASK_POLICY_ALL_SOCKETS_BG = 0x37
    IMP_TASK_POLICY_BASE_LATENCY_AND_THROUGHPUT_QOS = 0x39  # /* latency as value1, throughput as value2 */
    IMP_TASK_POLICY_OVERRIDE_LATENCY_AND_THROUGHPUT_QOS = 0x3A  # /* latency as value1, throughput as value2 */
    IMP_TASK_POLICY_PIDBIND_BG = 0x32
    IMP_TASK_POLICY_QOS_OVERRIDE = 0x36
    IMP_TASK_POLICY_QOS_AND_RELPRIO = 0x38  # /* QoS as value1, relative priority as value2 */
    IMP_TASK_POLICY_QOS_WORKQ_OVERRIDE = 0x3B
    IMP_TASK_POLICY_QOS_PROMOTE = 0x3C
    IMP_TASK_POLICY_QOS_KEVENT_OVERRIDE = 0x3D
    IMP_TASK_POLICY_QOS_SERVICER_OVERRIDE = 0x3E


class IMP_ASSERTION(enum.Enum):
    IMP_HOLD = 0x2  # /* Task holds a boost assertion */
    IMP_DROP = 0x4  # /* Task drops a boost assertion */
    IMP_EXTERN = 0x8  # /* boost assertion moved from kernel to userspace responsibility (externalized) */


class IMP_BOOST(enum.Enum):
    IMP_BOOSTED = 0x1
    IMP_UNBOOSTED = 0x2  # /* Task drops a boost assertion */


class IMP_MSG(enum.Enum):
    IMP_MSG_SEND = 0x1  # /* boosting message sent by donating task on donating port */
    IMP_MSG_DELV = 0x2  # /* boosting message delivered to task */


class IMP_UPDATE(enum.Enum):
    IMP_UPDATE_TASK_CREATE = 0x1


class IMP_USYNCH_QOS_OVERRIDE(enum.Enum):
    IMP_USYNCH_ADD_OVERRIDE = 0x0  # /* add override for a contended resource */
    IMP_USYNCH_REMOVE_OVERRIDE = 0x1  # /* remove override for a contended resource */


class IMP_DONOR_CHANGE(enum.Enum):
    IMP_DONOR_UPDATE_LIVE_DONOR_STATE = 0x0
    IMP_DONOR_INIT_DONOR_STATE = 0x1


class IMP_SYNC_IPC_QOS(enum.Enum):
    IMP_SYNC_IPC_QOS_APPLIED = 0x0
    IMP_SYNC_IPC_QOS_REMOVED = 0x1
    IMP_SYNC_IPC_QOS_OVERFLOW = 0x2
    IMP_SYNC_IPC_QOS_UNDERFLOW = 0x3


class DBG_TURNSTILE(enum.Enum):
    TURNSTILE_HEAP_OPERATIONS = 0x10
    TURNSTILE_PRIORITY_OPERATIONS = 0x20
    TURNSTILE_FREELIST_OPERATIONS = 0x30


class TURNSTILE_HEAP_OPERATIONS(enum.Enum):
    THREAD_ADDED_TO_TURNSTILE_WAITQ = 0x1
    THREAD_REMOVED_FROM_TURNSTILE_WAITQ = 0x2
    THREAD_MOVED_IN_TURNSTILE_WAITQ = 0x3
    TURNSTILE_ADDED_TO_TURNSTILE_HEAP = 0x4
    TURNSTILE_REMOVED_FROM_TURNSTILE_HEAP = 0x5
    TURNSTILE_MOVED_IN_TURNSTILE_HEAP = 0x6
    TURNSTILE_ADDED_TO_THREAD_HEAP = 0x7
    TURNSTILE_REMOVED_FROM_THREAD_HEAP = 0x8
    TURNSTILE_MOVED_IN_THREAD_HEAP = 0x9
    TURNSTILE_UPDATE_STOPPED_BY_LIMIT = 0xa
    THREAD_NOT_WAITING_ON_TURNSTILE = 0xb


class TURNSTILE_PRIORITY_OPERATIONS(enum.Enum):
    TURNSTILE_PRIORITY_CHANGE = 0x1
    THREAD_USER_PROMOTION_CHANGE = 0x2


class TURNSTILE_FREELIST_OPERATIONS(enum.Enum):
    TURNSTILE_PREPARE = 0x1
    TURNSTILE_COMPLETE = 0x2


class DBG_BANK(enum.Enum):
    BANK_ACCOUNT_INFO = 0x10  # /* Trace points related to bank account struct */
    BANK_TASK_INFO = 0x11  # /* Trace points related to bank task struct */


class DBG_ATM(enum.Enum):
    ATM_SUBAID_INFO = 0x10
    ATM_GETVALUE_INFO = 0x20
    ATM_UNREGISTER_INFO = 0x30


class BANK_ACCOUNT_INFO(enum.Enum):
    BANK_SETTLE_CPU_TIME = 0x1  # /* Bank ledger(chit) rolled up to tasks. */
    BANK_SECURE_ORIGINATOR_CHANGED = 0x2  # /* Secure Originator changed. */
    BANK_SETTLE_ENERGY = 0x3  # /* Bank ledger(energy field) rolled up to tasks. */


class ATM_SUBAID_INFO(enum.Enum):
    ATM_MIN_CALLED = 0x1
    ATM_LINK_LIST_TRIM = 0x2


class ATM_GETVALUE_INFO(enum.Enum):
    ATM_VALUE_REPLACED = 0x1
    ATM_VALUE_ADDED = 0x2


class ATM_UNREGISTER_INFO(enum.Enum):
    ATM_VALUE_UNREGISTERED = 0x1
    ATM_VALUE_DIFF_MAILBOX = 0x2


class DBG_DAEMON(enum.Enum):
    DBG_DAEMON_COREDUET = 0x1
    DBG_DAEMON_POWERD = 0x2


# 0x7000004	TRACE_DATA_NEWTHREAD
# 0x7000008	TRACE_DATA_EXEC
# 0x700000c	TRACE_DATA_THREAD_TERMINATE
# 0x7000010	TRACE_DATA_THREAD_TERMINATE_PID
# 0x7010000	TRACE_STRING_GLOBAL
# 0x7010004	TRACE_STRING_NEWTHREAD
# 0x7010008	TRACE_STRING_EXEC
# 0x701000c	TRACE_STRING_PROC_EXIT
# 0x7010010	TRACE_STRING_THREADNAME
# 0x7010014	TRACE_STRING_THREADNAME_PREV

def trace_data_new_thread(parser, data):
    parser.threads_pids[data.args[0]] = data.args[1]


def trace_data_exec(parser, data):
    parser.threads_pids[data.tid] = data.args[0]


def trace_string_new_thread(parser, data):
    name = data.buf_data.replace(b'\x00', b'').decode()
    parser.tid_names[data.tid] = name
    pid = parser.threads_pids.get(data.tid)
    if pid:
        parser.pid_names[pid] = name


def trace_string_exec(parser, data):
    name = data.buf_data.replace(b'\x00', b'').decode()
    parser.tid_names[data.tid] = name
    pid = parser.threads_pids.get(data.tid)
    if pid:
        parser.pid_names[pid] = name


def trace_string_proc_exit(parser, data):
    name = data.buf_data.replace(b'\x00', b'').decode()
    return name


def trace_string_thread_name(parser, data):
    name = data.buf_data.replace(b'\x00', b'').decode()
    parser.tids_names[data.tid] = name


def trace_string_thread_name_prev(parser, data):
    name = data.buf_data.replace(b'\x00', b'').decode()
    parser.tids_names[data.tid] = name


def trace_unknown(parser, data):
    pass


trace_handlers = {
    0x7000004: trace_data_new_thread,
    0x7000008: trace_data_exec,
    # 0x700000c: trace_unknown,
    # 0x7000010: trace_unknown,
    # 0x7010000: trace_unknown,
    0x7010004: trace_string_new_thread,
    0x7010008: trace_string_exec,
    0x701000c: trace_string_proc_exit,
    0x7010010: trace_string_thread_name,
    0x7010014: trace_string_thread_name_prev,
    # 0x7020000: trace_unknown,
    # 0x7020004: trace_unknown,
    # 0x7020008: trace_unknown
}


def decode_trace_data(parser, data):
    if isinstance(data, KdBufParser):
        fun = trace_handlers.get(data.debug_id)
        if fun:
            fun(parser, data)


kd_threadmap = Struct(
    'tid' / Int64ul,
    'pid' / Int32ul,
    'process' / FixedSized(0x14, CString('utf8')),
)

kd_header_v2 = Struct(
    'tag' / Int32ul,
    'number_of_treads' / Int32ul,
    Padding(12),
    'is_64bit' / Int32ul,
    'tick_frequency' / Int64ul,
    Padding(0x100),
    'threadmap' / Array(lambda ctx: ctx.number_of_treads, kd_threadmap),
    '_pad' / GreedyRange(Const(0, Byte)),
)


class BplistAdapter(Adapter):
    def _decode(self, obj, context, path):
        return plistlib.loads(obj)

    def _encode(self, obj, context, path):
        return plistlib.dumps(obj)


class KCdataParse(Adapter):

    def _decode(self, obj, context, path):
        return kc_data_parse(obj)


kd_header_v3 = Struct(
    'tag' / Int32ul,
    'sub_tag' / Int32ul,
    'length' / Int64ul,
    'timebase_numer' / Int32ul,
    'timebase_denom' / Int32ul,
    'timestamp' / Int64ul,
    'walltime_secs' / Int64ul,
    'walltime_usecs' / Int32ul,
    'timezone_minuteswest' / Int32ul,
    'timezone_dst' / Int32ul,
    'flags' / Int32ul,
)

CLASS_DICT = vars()


class KdBufParser:

    def __init__(self, timestamp, args_buf, tid, debug_id, cpuid, unused):
        self.timestamp = timestamp
        self.args = struct.unpack('<QQQQ', args_buf)
        self.buf_data = args_buf
        self.tid = tid
        self.cpuid = cpuid
        self.unused = unused
        self.debug_id = debug_id
        self.event_id = debug_id & KDBG_EVENTID_MASK
        self.func_code = debug_id & KDBG_FUNC_MASK
        self.class_code = kdbg_extract_class(debug_id)
        self.subclass_code = kdbg_extract_subclass(debug_id)
        self.final_code = kdbg_extract_code(debug_id)

    @classmethod
    def decode(cls, parser, buf_io: io.BytesIO):
        while True:
            buf = buf_io.read(64)
            if not buf:
                return
            _cls = cls(*struct.unpack(KD_BUF_FORMAT, buf))
            decode_trace_data(parser, _cls)
            yield _cls


def _format_class(classes, code):
    if classes:
        try:
            classes_name = classes(code).name
            return classes_name, f'{classes_name:<18}'
        except ValueError:
            return None, f'''{'Error(' + (str(code)) + ")"}'''
    else:
        return None, f'''{'Error(' + (str(code)) + ")"}'''


SSHOT_TAG = 0x8002
IMAGES_TAG = 0x8004
KERNEL_EXTENSIONS_TAG = 0x8005
CONFIG_TAG = 0x8006
KERNEL_TAG = 0x8008
MACHINE_TAG = 0x8c00
CPU_EVENTS_TAG = 0x8c01
CPU_EVENTS_TAG2 = 0x8013
CPU_EVENTS_NULL = 0x800e
RAW_VERSION3 = 0x00001000
V3_NULL_CHUNK = 0x00002000
V3_CONFIG = 0x00001b00
V3_CPU_HEADER_TAG = 0x00001c00
V3_THREAD_MAP = 0x00001d00
V3_RAW_EVENTS = 0x00001e00

kd_cpumap = Struct(
    'cpu_id' / Int32ul,
    'flags' / Int32ul,
    'name' / FixedSized(8, CString('utf8')),
    'args' / Array(6, Int32ul),
)

kd_cpumap_header = Struct(
    'version_no' / Int32ul,
    'cpu_count' / Int32ul,
)

ktrace_pack = Struct(
    'tag' / Int32ul,
    'major' / Int16ul,
    'minor' / Int16ul,
    'length' / Int64ul,
    'data' / Switch(this.tag,
                    {MACHINE_TAG: FixedSized(this.length, BplistAdapter(GreedyBytes)),
                     CONFIG_TAG: FixedSized(this.length, BplistAdapter(GreedyBytes)),
                     KERNEL_TAG: FixedSized(this.length, BplistAdapter(GreedyBytes)),
                     KERNEL_EXTENSIONS_TAG: FixedSized(this.length, BplistAdapter(GreedyBytes)),
                     IMAGES_TAG: FixedSized(this.length, BplistAdapter(GreedyBytes)),
                     SSHOT_TAG: FixedSized(this.length, KCdataParse(GreedyBytes)),
                     CPU_EVENTS_TAG: FixedSized(this.length, GreedyBytes),
                     CPU_EVENTS_TAG2: FixedSized(this.length, GreedyBytes),
                     CPU_EVENTS_NULL: FixedSized(this.length, GreedyBytes),
                     V3_NULL_CHUNK: FixedSized(this.length, GreedyBytes),
                     V3_RAW_EVENTS: FixedSized(this.length, GreedyBytes),
                     V3_CPU_HEADER_TAG: kd_cpumap_header,
                     V3_THREAD_MAP: FixedSized(this.length, GreedyRange(kd_threadmap))},
                    default=GreedyBytes),
)


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


class KperfData:
    def __init__(self, traceCodesFile={}, filter_pid=None, filter_process=None):
        self.machine_info = None
        self.cpu_header = None
        self.kd_cpu_map = None
        self.report_config = None
        self.ktrace_config = None
        self.kd_header_v3 = None
        self.stack_shot = None
        self.trace_codes = traceCodesFile
        self.threads_pids = {}
        self.pid_names = {}
        self.tid_names = {}
        self.version = None
        self.filter_tid = filter_pid
        self.filter_process = filter_process

    def set_threads_pids(self, threads):
        for thread in threads:
            self.pid_names[thread.pid] = thread.process
            self.tid_names[thread.tid] = thread.process
            self.threads_pids[thread.tid] = thread.pid

    def _format_process(self, tid):
        pid = self.threads_pids.get(tid)
        process_name = self.tid_names.get(tid)
        return pid, process_name, f'{process_name}({pid})' if pid else f'Error: tid {tid}'

    def parse(self, kd_buf: bytes):
        buf_io = io.BytesIO(kd_buf)
        version = kd_buf[:4]
        if version == b'\x07X\xa2Y':
            yield kc_data_parse(buf_io.read())
        elif version == VERSION2_FLAG:
            yield from self._parse_v2(buf_io)
        elif version == VERSION3_FLAG:
            yield from self._parse_v2(buf_io)
        else:
            yield from KdBufParser.decode(self, buf_io)

    def _parse_v2(self, buf_io: io.BytesIO):
        parsed_header = kd_header_v2.parse_stream(buf_io)
        self.set_threads_pids(parsed_header.threadmap)
        yield from KdBufParser.decode(self, buf_io)

    def _parse_v3(self, buf_io: io.BytesIO):
        self.kd_header_v3 = kd_header_v3.parse_stream(buf_io)
        while True:
            try:
                raw_events = ktrace_pack.parse_stream(buf_io)
            except StreamError:
                break
            if raw_events.tag in (V3_NULL_CHUNK, CPU_EVENTS_NULL):
                continue
            elif raw_events.tag == CONFIG_TAG:
                self.ktrace_config = raw_events
                GreedyRange(Const(0, Byte)).parse_stream(buf_io)
            elif raw_events.tag == KERNEL_TAG:
                self.report_config = raw_events
                GreedyRange(Const(0, Byte)).parse_stream(buf_io)
            elif raw_events.tag == SSHOT_TAG:
                self.stack_shot = raw_events
            elif raw_events.tag == V3_THREAD_MAP:
                self.set_threads_pids(raw_events.data)
            elif raw_events.tag == MACHINE_TAG:
                self.machine_info = raw_events
                GreedyRange(Const(0, Byte)).parse_stream(buf_io)
            elif raw_events.tag == V3_CPU_HEADER_TAG:
                self.cpu_header = raw_events
                self.kd_cpu_map = FixedSized(raw_events.length - kd_cpumap_header.sizeof(),
                                             GreedyRange(kd_cpumap)).parse_stream(buf_io)
            elif raw_events.tag == V3_RAW_EVENTS:
                events_buf = io.BytesIO(raw_events.data)
                events_buf.read(8)  # Future events timestamp struct.pack('Q', 0)
                yield from KdBufParser.decode(self, buf_io)

    def to_dict(self, kd_buf):
        for event in self.parse(kd_buf):
            yield event

    def to_str(self, kd_buf: bytes):
        for event in self.parse(kd_buf):
            if not isinstance(event, KdBufParser):
                yield event
                return
            pid, process_name, process_str = self._format_process(event.tid)
            if self.filter_tid and self.filter_tid != pid:
                continue
            if self.filter_process and self.filter_process != process_name:
                continue
            formatted_data = ''
            formatted_data += f'{process_str:<27}'
            if event.event_id in self.trace_codes:
                name = self.trace_codes[event.event_id] + f' ({hex(event.event_id)})'
            else:
                name = hex(event.event_id)

            formatted_data += f'{name:<60}'
            classes_name, _str = _format_class(DebugClasses, event.class_code)
            formatted_data += f'{_str:<18}'
            classes_name, _str = _format_class(CLASS_DICT.get(classes_name), event.subclass_code)
            formatted_data += f'{_str:<30}'
            try:
                formatted_data += f'{DgbFuncQual(event.func_code).name:<15}'
            except ValueError:
                formatted_data += f'{"Error":<16}'
            yield formatted_data

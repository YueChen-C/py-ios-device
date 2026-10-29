"""把 kdebug 生命周期事件还原成 App 启动阶段时间线。

规则来自 Instruments 的 ``com.apple.dt.app-life-cycle.dtac`` 扩展
（``modeling-rules/rules-0004.clp`` 的启动阶段规则 + ``rules-0003.clp`` 的区间记账）。

    lc = AppLifeCycle(machTimeInfo, usecs_since_epoch)
    for event in kperf.to_dict(data):
        if lc.decode_app_lifecycle(event, pid):   # 只收集，不打印
            lc.format_str()                       # 启动结束，输出一次

Instruments 用 CLIPS 事实库，天然不依赖事件顺序；旧实现边收边配对边打印，所以
END 先到、缺 END、首条事件不是 start 都会让整份报告消失。这里先缓冲、再按时间戳
重放配对，乱序或截断最多只是少一行或标一个 ``(open)``。
"""

from collections import defaultdict, namedtuple
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Hashable, Optional

from ios_device.util import Log
from ios_device.util.variables import LOG

if TYPE_CHECKING:  # 仅用于类型标注，运行时不依赖 kperf_data（避免 construct 依赖）
    from ios_device.util.kperf_data import KdBufParser

log = Log.getLogger(LOG.Instrument.value)

__all__ = ['AppLifeCycle', 'AppLifeEvent', 'AppLifeInterval', 'Period', 'SubState', 'Kind',
           'UIKind', 'format_duration', 'convertTime', 'SUBSCRIBED_CLASSES']

_UNITS = ('ns', 'us', 'ms', 's')


# ---- 词汇表：字符串同时是输出的一部分，名字与 .dtac 的槽位一一对应 ----
class Period:
    INITIALIZING = 'Initializing'
    LAUNCHING = 'Launching'
    EXEC = 'Exec'


class SubState:
    # 扩展里叫 "System Interface Initialization"；保留后缀是为了不破坏已有输出
    SYSTEM_INTERFACE_INIT = 'System Interface Initialization (Dyld init)'
    STATIC_RUNTIME_INIT = 'Static Runtime Initialization'
    APPKIT_INIT = 'AppKit Initialization'
    APPKIT_SCENE = 'AppKit Scene Creation'
    APPKIT_WILL_FINISH = 'applicationWillFinishLaunching()'
    APPKIT_DID_FINISH = 'applicationDidFinishLaunching()'
    UIKIT_INIT = 'UIKit Initialization'
    UIKIT_SCENE = 'UIKit Scene Creation'
    UIKIT_WILL_FINISH = 'willFinishLaunchingWithOptions()'
    UIKIT_DID_FINISH = 'didFinishLaunchingWithOptions()'
    SCENE_WILL_CONNECT = 'sceneWillConnectTo()'
    SCENE_WILL_ENTER_FOREGROUND = 'sceneWillEnterForeground()'
    INITIAL_FRAME = 'Initial Frame Rendering'
    PROCESS_EXEC = 'Process Exec'


class Kind:
    BEGIN = 'BEGIN'
    END = 'END'


class UIKind:
    # main-ui-thread 的类型，决定同一事件按 AppKit 还是 UIKit 解释
    APPKIT = 'APPKIT'
    UIKIT = 'UIKIT'
    MARZIPAN = 'MARZIPAN'


# main-ui-thread 尚未判定（None 已被 rule(ui_when=...) 用作"不限"，所以另设哨兵）
UI_UNSET = 'UNSET'

# 规则表里的简写，值仍然来自 Period
LAUNCHING, INITIALIZING, EXEC = Period.LAUNCHING, Period.INITIALIZING, Period.EXEC


# ---- 数据结构 ----
# 一条 update-app-period 事实；time 是原始 kdebug 时间戳，thread 是调用方的分组键
AppLifeEvent = namedtuple('AppLifeEvent', 'period sub_state time thread kind code')

# 求解后的区间；begin/end/duration 是相对 mach base 的整数纳秒，
# closed=False 表示出报告时还没等到 END（end 取最后一个事件时间）
AppLifeInterval = namedtuple('AppLifeInterval', 'period sub_state begin end duration thread closed')

_OpenInterval = namedtuple('_OpenInterval', 'period sub_state start')
_Change = namedtuple('_Change', 'kind period sub_state dt')

# 同一时间戳上先处理 END：阶段切换就是"先结束旧的、再开始新的"
_KIND_ORDER = {Kind.END: 0, Kind.BEGIN: 1}


# ---- 规则：kdebug 签名 → 阶段变更 ----
# 键是 (kdebug class, subclass)；同一键下的规则按声明顺序匹配，扩展正是用这个顺序
# 区分同一事件的两种含义（纯 AppKit vs Marzipan）。
def begin(period, sub_state):
    return _Change(Kind.BEGIN, period, sub_state, 0)


def end(period, sub_state, dt=0):
    """dt 是 kdebug tick 偏移，负数表示提前收口。"""
    return _Change(Kind.END, period, sub_state, dt)


def next_phase(period, previous, following, gap=1):
    """结束 previous、开始 following —— 规则表里最常见的形态。

    扩展统一用 (- ?time 1) 结束上一个阶段避免区间重叠，所以默认提前 1 tick。
    """
    return [end(period, previous, dt=-gap), begin(period, following)]


# code/func/arg1 是签名过滤条件（None=不限，等价于 CLIPS 里不写该槽位）；
# ui_when 要求当前 main-ui-thread 类型，命中后 ui_kind 会更新它；
# detector=启动开始事件，finishes=启动结束事件（清掉 UI 类型，等下一次启动）。
_Rule = namedtuple('_Rule', 'code changes func arg1 ui_when ui_kind detector finishes')


def rule(code, changes, func=None, arg1=None, ui_when=None, ui_kind=None,
         detector=False, finishes=False):
    return _Rule(code, tuple(changes), func, arg1, ui_when, ui_kind, detector, finishes)


def _matches(rule, event, ui_kind):
    if event.final_code != rule.code:
        return False
    if rule.func is not None and event.func_code != rule.func:
        return False
    if rule.arg1 is not None and not (event.args and event.args[0] == rule.arg1):
        return False
    return rule.ui_when is None or ui_kind == rule.ui_when


_LAUNCH_RULES = {
    # DBG_DYLD：dyld 初始化
    (0x1f, 0x07): [
        rule(13, [begin(INITIALIZING, SubState.SYSTEM_INTERFACE_INIT)], detector=True),
        # 扩展里 dyld-init-end 和 before-main-init-end 匹配同一事件，会连发两个 END；
        # 求解时只会关掉当时真正打开的那个 "Initializing"
        rule(1, [end(INITIALIZING, SubState.SYSTEM_INTERFACE_INIT),
                 end(INITIALIZING, SubState.STATIC_RUNTIME_INIT)], func=2),
    ],

    # DBG_TRACE：exec。扩展不把它当启动标志，但我们主动拉起的进程里它是最早的可靠
    # 事件，用它做 detector 可以避免每次误报"没抓到启动开头"
    (0x07, 0x00): [
        rule(2, [begin(EXEC, SubState.PROCESS_EXEC)], detector=True),
    ],

    # DBG_ARIADNE / appkit-init：Mac 与 Catalyst 应用
    (0x2b, 0xd8): [
        # 第一次出现：纯 AppKit；已经见过 UIKit 初始化：其实是 Marzipan
        rule(1, [begin(LAUNCHING, SubState.APPKIT_INIT)],
             func=0, ui_when=UI_UNSET, ui_kind=UIKind.APPKIT, detector=True),
        rule(1, [end(LAUNCHING, SubState.UIKIT_INIT), begin(LAUNCHING, SubState.APPKIT_INIT)],
             func=0, ui_when=UIKind.UIKIT, ui_kind=UIKind.MARZIPAN),
        rule(12, next_phase(LAUNCHING, SubState.APPKIT_INIT, SubState.APPKIT_SCENE, gap=0), func=0),
        rule(10, next_phase(LAUNCHING, SubState.APPKIT_SCENE, SubState.APPKIT_WILL_FINISH), func=1),
        rule(10, next_phase(LAUNCHING, SubState.APPKIT_WILL_FINISH, SubState.APPKIT_SCENE), func=2),
        rule(11, next_phase(LAUNCHING, SubState.APPKIT_SCENE, SubState.APPKIT_DID_FINISH), func=1),
        rule(11, next_phase(LAUNCHING, SubState.APPKIT_DID_FINISH, SubState.INITIAL_FRAME),
             func=2, ui_when=UIKind.APPKIT),
        rule(11, next_phase(LAUNCHING, SubState.APPKIT_DID_FINISH, SubState.APPKIT_SCENE),
             func=2, ui_when=UIKind.MARZIPAN),
    ],

    # DBG_ARIADNE / uikit-init：iOS 应用
    (0x2b, 0x87): [
        rule(90, [begin(LAUNCHING, SubState.UIKIT_INIT)],
             arg1=0x32, ui_kind=UIKind.UIKIT, detector=True),
        rule(21, next_phase(LAUNCHING, SubState.UIKIT_INIT, SubState.UIKIT_SCENE),
             ui_when=UIKind.UIKIT),
        rule(21, next_phase(LAUNCHING, SubState.APPKIT_SCENE, SubState.UIKIT_SCENE),
             ui_when=UIKind.MARZIPAN),
        rule(23, next_phase(LAUNCHING, SubState.UIKIT_SCENE, SubState.UIKIT_WILL_FINISH)),
        rule(24, next_phase(LAUNCHING, SubState.UIKIT_WILL_FINISH, SubState.UIKIT_SCENE)),
        rule(25, next_phase(LAUNCHING, SubState.UIKIT_SCENE, SubState.UIKIT_DID_FINISH)),
        rule(26, next_phase(LAUNCHING, SubState.UIKIT_DID_FINISH, SubState.UIKIT_SCENE)),
        rule(300, next_phase(LAUNCHING, SubState.UIKIT_SCENE, SubState.SCENE_WILL_CONNECT)),
        rule(301, next_phase(LAUNCHING, SubState.SCENE_WILL_CONNECT, SubState.UIKIT_SCENE)),
        rule(312, next_phase(LAUNCHING, SubState.UIKIT_SCENE, SubState.SCENE_WILL_ENTER_FOREGROUND)),
        rule(313, next_phase(LAUNCHING, SubState.SCENE_WILL_ENTER_FOREGROUND, SubState.UIKIT_SCENE)),
        # 扩展里这个事件不限制 function
        rule(12, next_phase(LAUNCHING, SubState.UIKIT_SCENE, SubState.INITIAL_FRAME)),
    ],

    # DBG_ARIADNE / before-main-init：dyld 初始化结束、静态初始化开始
    (0x2b, 0xdc): [
        rule(4, [end(INITIALIZING, SubState.SYSTEM_INTERFACE_INIT, dt=-1),
                 begin(INITIALIZING, SubState.STATIC_RUNTIME_INIT)], func=0, arg1=10),
    ],

    # AppKit/UIKit 共用：首帧渲染完成，一次启动到此结束
    (0x31, 0xca): [
        rule(1, [end(LAUNCHING, SubState.INITIAL_FRAME)], func=2, finishes=True),
    ],
}

#: 本模块会消费的 (kdebug class, subclass)，对应 binding-rules.clp 的订阅列表
SUBSCRIBED_CLASSES = frozenset(_LAUNCH_RULES)


# ---- 时间与格式化 ----
def format_duration(nanoseconds) -> str:
    """纳秒 → ``1.50 ms`` 这样的字符串；负数带符号。

    旧实现用 math.log，负时长会抛 ValueError，999999 ns 还会显示成 1000.00 us。
    """
    ns = int(round(nanoseconds))
    value, unit = float(abs(ns)), 0
    while unit < len(_UNITS) - 1 and round(value, 2) >= 1000.0:
        value /= 1000.0
        unit += 1
    return f'{"-" if ns < 0 else ""}{value:.2f} {_UNITS[unit]}'


convertTime = format_duration  # 旧名字，保留


def _read_timebase(mach_time_info):
    """machTimeInfo 数组 → (mach_absolute_time, numer, denom)，非法时退化为 tick。"""
    try:
        base, numer, denom = (int(value) for value in mach_time_info[:3])
    except (TypeError, ValueError, IndexError, KeyError):
        log.warning('invalid machTimeInfo %r, falling back to ticks', mach_time_info)
        return 0, 1, 1
    if numer <= 0 or denom <= 0:
        log.warning('invalid mach time base %r/%r, falling back to ticks', numer, denom)
        return base, 1, 1
    return base, numer, denom


# ---- 求解：事件 → 区间 ----
def _build_intervals(events, to_ns):
    """把一个进程的事件按时间戳重放成区间，返回 (intervals, problems)。

    按时间戳而不是到达顺序排序，所以 END 先到也能配对；同一个 period 同时最多只有
    一个打开的区间（与 open-app-period 一致），END 不必和 BEGIN 的 sub_state 相同。
    """
    thread = events[0].thread
    ordered = sorted(events, key=lambda item: (item.time, _KIND_ORDER[item.kind]))
    horizon = ordered[-1].time
    opened = {}   # period -> _OpenInterval
    seen = set()  # 出现过的 period，用来判断未配对的 END 值不值得报警
    intervals, problems = [], []

    def build(current, end_time, closed):
        begin_ns = to_ns(current.start)
        end_ns = to_ns(max(end_time, current.start))
        return AppLifeInterval(current.period, current.sub_state,
                               begin_ns, end_ns, end_ns - begin_ns, thread, closed)

    def close(period, end_time):
        intervals.append(build(opened.pop(period), end_time, True))

    for event in ordered:
        if event.kind == Kind.END:
            if event.period not in opened:
                # 该 period 从没开过才提示：dyld-init-end 会故意多发一个 END
                if event.period not in seen:
                    problems.append(f'[{thread!r}] END for {event.period}/{event.sub_state} '
                                    f'without a matching BEGIN; dropped')
                continue
            close(event.period, event.time)
            continue

        # 其余按 BEGIN 处理（本模块只产生 BEGIN/END）
        if EXEC in opened and event.period != EXEC:
            # Exec 没有 END 事件，由下一个阶段开始截断（end-exec-interval）
            close(EXEC, event.time)

        current = opened.get(event.period)
        if current is None:
            opened[event.period] = _OpenInterval(event.period, event.sub_state, event.time)
            seen.add(event.period)
        elif current.sub_state == event.sub_state:
            problems.append(f'[{thread!r}] duplicate BEGIN for '
                            f'{event.period}/{event.sub_state} ignored')
        else:
            # 少了 END：在上一个阶段起点收口，避免整条时间线错位
            problems.append(f'[{thread!r}] BEGIN for {event.period}/{event.sub_state} while '
                            f'{event.period}/{current.sub_state} was still open; closed it at '
                            f'the new BEGIN (missing END event)')
            close(event.period, event.time)
            opened[event.period] = _OpenInterval(event.period, event.sub_state, event.time)

    # 出报告时仍未闭合：截到最后一个事件，标记 closed=False
    for current in opened.values():
        intervals.append(build(current, horizon, False))

    intervals.sort(key=lambda item: (item.begin, item.end))
    return intervals, problems


def _print_report(intervals, describe=None):
    """按进程打印瀑布图 + 总耗时。"""
    grouped = {}
    for interval in intervals:
        grouped.setdefault(interval.thread, []).append(interval)

    for key, rows in grouped.items():
        if isinstance(key, (tuple, list)):
            ident, name = key[0], (key[1] if len(key) > 1 else '')
        else:
            ident, name = key, ''
        if describe is not None:
            name = describe(key) or name
        for row in rows:
            suffix = '' if row.closed else '  (open)'
            print(f'{format_duration(row.duration):>10}   {row.period}-{row.sub_state}{suffix}')
        total = max(row.end for row in rows) - min(row.begin for row in rows)
        print(f'App Thread Process ID:{ident} Name:{name}, '
              f'Process Total Time:{format_duration(total)}')


# ---- 对外接口 ----
class AppLifeCycle:
    """采集 kdebug 事件并输出启动阶段。

    ``process_key`` 是可哈希的分组键，建议直接用 pid：不要带进程名，因为名字可能到
    采集中途才解析出来，那样同一场 launch 会被拆成两组、各自只报一半。
    """

    def __init__(self, machTimeInfo, usecs_since_epoch=0):
        self.mach_absolute_time, self.numer, self.denom = _read_timebase(machTimeInfo)
        self.usecs_since_epoch = int(usecs_since_epoch or 0)
        self.events = defaultdict(list)   # process_key -> [AppLifeEvent]
        self.warnings = []                # 建模/求解过程中发现的问题
        self._ui_kind = {}                # process_key -> UIKind / UI_UNSET
        self._launching = set()           # 已知处在启动过程中的 process_key

    def decode_app_lifecycle(self, event: 'KdBufParser',
                             process_key: Optional[Hashable] = None) -> bool:
        """翻译一条 kdebug 事件；整段启动结束时返回 True（该打印报告的时机）。

        不属于本模块的事件返回 False 且不入缓存，调用方不必自己按 class 过滤。
        """
        if process_key is None:
            process_key = event.tid
        rules = _LAUNCH_RULES.get((event.class_code, event.subclass_code))
        ui_kind = self._ui_kind.get(process_key, UI_UNSET)
        matched = next((r for r in (rules or ()) if _matches(r, event, ui_kind)), None)
        if matched is None:
            return False

        if not event.timestamp:
            self._warn(f'ignored kdebug {event.debug_id:#010x}: timestamp is 0')
            return False
        if matched.finishes and not self.events.get(process_key):
            # 没有正在跟的 launch，孤立的收尾事件不处理（扩展需要 app-launching 事实）
            return False

        if matched.detector:
            self._launching.add(process_key)
        elif not self.events.get(process_key) and process_key not in self._launching:
            self._warn(f'first lifecycle event for {process_key!r} is '
                       f'{event.class_code:#04x}/{event.subclass_code:#04x} code {event.final_code}; '
                       f'the launch detector was never observed, so the launch start is unknown')

        for change in matched.changes:
            self.events[process_key].append(AppLifeEvent(
                change.period, change.sub_state, event.timestamp + change.dt,
                process_key, change.kind, event.debug_id))

        if matched.ui_kind:
            self._ui_kind[process_key] = matched.ui_kind
        if matched.finishes:
            self._ui_kind.pop(process_key, None)
            self._launching.discard(process_key)
            return True
        return False

    def update_app_period(self, data: AppLifeEvent):
        """直接塞一条阶段事件（扩展点/测试用）。"""
        self.events[data.thread].append(data)

    def finish(self) -> list:
        """把缓存的事件求解成区间列表，不清状态（可重复调用）。"""
        intervals = []
        for process_key in list(self.events):
            rows, problems = _build_intervals(self.events[process_key], self.format_timestamp)
            intervals.extend(rows)
            for problem in problems:
                self._warn(problem)
        intervals.sort(key=lambda item: (item.begin, item.end))
        return intervals

    def format_str(self, clear: bool = True, describe=None) -> list:
        """打印瀑布图并返回区间；``clear=True`` 时打印后清空，便于收尾和结束时各调一次。

        ``describe`` 是可选的 ``key -> name`` 回调，用来在打印时补上进程名——名字可能
        比事件晚到，所以不放进分组键。
        """
        intervals = self.finish()
        if intervals:
            _print_report(intervals, describe)
        if clear:
            self.reset()
        return intervals

    def reset(self):
        """清空缓存、建模状态和告警。"""
        self.events.clear()
        self.warnings.clear()
        self._ui_kind.clear()
        self._launching.clear()

    def format_timestamp(self, timestamp) -> int:
        """mach 时间戳 → 相对 mach base 的整数纳秒。"""
        return (int(timestamp) - self.mach_absolute_time) * self.numer // self.denom

    def wall_time(self, timestamp=None) -> Optional[datetime]:
        """时间戳对应的 UTC 墙上时间；没有 ``usecs_since_epoch`` 时返回 None。"""
        if not self.usecs_since_epoch:
            return None
        timestamp = self.mach_absolute_time if timestamp is None else timestamp
        micros = self.usecs_since_epoch + self.format_timestamp(timestamp) // 1000
        return datetime.fromtimestamp(micros / 1_000_000, tz=timezone.utc)

    def _warn(self, message):
        # 相同的告警只记一次：消息种类有限，不必再做条数上限
        if message not in self.warnings:
            self.warnings.append(message)
            log.warning(message)

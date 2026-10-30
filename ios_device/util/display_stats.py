"""按帧事件统计 fps / 卡顿 / 严重卡顿 / 卡顿率。

口径沿用 PerfDog：

- 卡顿 Jank：这一帧的耗时 > 前三帧平均耗时的 2 倍，且 > 电影帧耗时(1/24s) 的 2 倍
- 严重卡顿 BigJank：> 前三帧平均耗时的 3 倍，且 > 电影帧耗时的 3 倍
- 卡顿率 Stutter：窗口内卡顿帧的总耗时 / 窗口总耗时

帧耗时 = 相邻两个帧事件（kdebug ``0x31/0x80/0xc6``）的 mach 时间戳差 × mach
timebase（``machTimeInfo`` 的 numer/denom，不是固定值）。
"""

from statistics import mean

NANO_SECOND = 1e9  # ns
#: PerfDog 卡顿口径里的基准帧耗时（秒）
MOVIE_FRAME_COST = 1 / 24

#: 帧事件（CA commit）的 kdebug 签名：(class, subclass, code)
FRAME_EVENT = (0x31, 0x80, 0xC6)


class DisplayStats:
    """把帧事件流聚成按窗口的 fps / 卡顿统计。

    ``add_frame`` 喂一个帧事件的 mach 时间戳，凑满一个窗口（默认 1 秒）时返回
    一份统计 dict，否则返回 ``None``。窗口按帧时间戳累计，不用宿主机墙钟，所以
    输出不受 tap 传输抖动影响。前三帧的耗时不随窗口重置，卡顿检测是连续的。
    """

    def __init__(self, mach_time_factor=125 / 3, window=1.0):
        """``mach_time_factor`` 是 mach tick → 纳秒 的比值，``window`` 是窗口秒数。"""
        self.factor = float(mach_time_factor)
        self.window_ns = window * NANO_SECOND
        self._last_frame = None  # 上一帧的 mach 时间戳
        self._costs = [0.0, 0.0, 0.0]  # 前三帧的耗时（纳秒）
        self._frames = 0  # 窗口内已计的帧数
        self._elapsed = 0.0  # 窗口内累计的帧耗时（纳秒）
        self._jank = 0
        self._big_jank = 0
        self._jank_time = 0.0  # 窗口内卡顿帧的总耗时（纳秒）

    def add_frame(self, timestamp):
        """喂一个帧事件的时间戳；凑满一个窗口时返回统计 dict，否则返回 ``None``。"""
        if self._last_frame is None or timestamp <= self._last_frame:
            # 第一帧只做基准；时间戳相同或倒退（重复事件 / 时间源重启）不计帧，
            # 否则 0 耗时的帧会拉高 fps，负耗时会算出负的 fps
            self._last_frame = timestamp
            return None

        cost = (timestamp - self._last_frame) * self.factor
        self._last_frame = timestamp
        self._frames += 1
        self._elapsed += cost

        if all(self._costs):  # 需要前三帧做基准
            average = mean(self._costs)
            if cost > average * 2 and cost > MOVIE_FRAME_COST * NANO_SECOND * 2:
                self._jank += 1
                self._jank_time += cost
                if cost > average * 3 and cost > MOVIE_FRAME_COST * NANO_SECOND * 3:
                    self._big_jank += 1

        self._costs = [self._costs[1], self._costs[2], cost]

        if self._elapsed < self.window_ns:
            return None
        return self._pop_report()

    def _pop_report(self):
        report = {
            # 窗口时长（秒），就是累计的帧耗时，不再用宿主机墙钟相减
            "time": round(self._elapsed / NANO_SECOND, 3),
            "fps": round(self._frames / self._elapsed * NANO_SECOND, 2),
            "jank": self._jank,
            "big_jank": self._big_jank,
            "stutter": round(self._jank_time / self._elapsed, 4),
        }
        self._frames = 0
        self._elapsed = 0.0
        self._jank = self._big_jank = 0
        self._jank_time = 0.0
        return report

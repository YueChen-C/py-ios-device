"""Unit tests for :mod:`ios_device.util.display_stats` and ``utils.kperf_data``.

Pure tests with synthetic frame timestamps; no device required.  They pin the
PerfDog-style jank rules and the window accounting that ``cmd_display`` /
``start_get_fps`` rely on, including the bugs that were fixed: the hardcoded
mach timebase and the cumulative (never reset) window time.
"""
import struct
import unittest

from ios_device.util.display_stats import DisplayStats, FRAME_EVENT, MOVIE_FRAME_COST, NANO_SECOND
from ios_device.util.kperf_data import kdbg_extract_all
from ios_device.util.utils import kperf_data

FACTOR = 125 / 3          # 24 MHz timebase: 1 tick == 125/3 ns
FRAME_MS = 1000 / 60      # 60 fps 帧间隔


def frames(costs_ms, factor=FACTOR, window=1.0):
    """喂一串帧间隔（毫秒），返回 (stats, reports)。

    第一个间隔只用来定位基准帧，不计入统计；之后每个间隔是一帧的耗时。
    """
    stats = DisplayStats(factor, window)
    reports = []
    timestamp = int(1e9)
    for cost in costs_ms:
        timestamp += int(round(cost * 1e6 / factor))
        report = stats.add_frame(timestamp)
        if report:
            reports.append(report)
    return stats, reports


class TestDisplayStats(unittest.TestCase):

    def test_steady_60fps(self):
        stats, reports = frames([FRAME_MS] * 125)
        self.assertEqual(len(reports), 2)
        for report in reports:
            self.assertAlmostEqual(report['fps'], 60.0, places=1)
            self.assertEqual(report['jank'], 0)
            self.assertEqual(report['big_jank'], 0)
            self.assertEqual(report['stutter'], 0.0)

    def test_time_is_the_window_duration_not_cumulative(self):
        """回归：旧实现里 last_time 从不重置，第二个窗口的 time 会是 2.0。"""
        _, reports = frames([FRAME_MS] * 125)
        self.assertEqual(len(reports), 2)
        for report in reports:
            self.assertGreater(report['time'], 0.9)
            self.assertLess(report['time'], 1.1)

    def test_jank_needs_both_conditions(self):
        # 100ms：> 前三帧均值的 2 倍，也 > 电影帧耗时的 2 倍
        _, reports = frames([FRAME_MS] * 4 + [100] + [FRAME_MS] * 60)
        self.assertEqual(reports[0]['jank'], 1)
        self.assertEqual(reports[0]['big_jank'], 0)
        self.assertGreater(reports[0]['stutter'], 0.05)
        self.assertLess(reports[0]['stutter'], 0.15)

    def test_big_jank(self):
        # 200ms：> 电影帧耗时的 3 倍(125ms)
        _, reports = frames([FRAME_MS] * 4 + [200] + [FRAME_MS] * 60)
        self.assertEqual(reports[0]['jank'], 1)
        self.assertEqual(reports[0]['big_jank'], 1)

    def test_slow_but_not_jank(self):
        # 60ms：是前三帧均值的 3.6 倍，但没超过电影帧耗时的 2 倍(83.3ms)
        _, reports = frames([FRAME_MS] * 4 + [60] + [FRAME_MS] * 60)
        self.assertEqual(reports[0]['jank'], 0)

    def test_warmup_frames_cannot_be_jank(self):
        # 前三帧没有历史可比较
        _, reports = frames([FRAME_MS, 200] + [FRAME_MS] * 61)
        self.assertEqual(reports[0]['jank'], 0)

    def test_duplicate_timestamp_is_not_a_frame(self):
        # 相同时间戳的重复事件不能计帧，否则 fps 会被抬高
        _, reports = frames([FRAME_MS, 0] + [FRAME_MS] * 61)
        self.assertEqual(reports[0]['fps'], 60.0)

    def test_window_is_reported_only_once_full(self):
        # factor=1：时间戳就是纳秒，100ms 一帧，凑满 10 帧才出报告
        stats = DisplayStats(1.0)
        step = int(1e8)
        stats.add_frame(step)
        for index in range(2, 11):  # 第 2..10 帧，累计 0.9s
            self.assertIsNone(stats.add_frame(index * step))
        self.assertIsNotNone(stats.add_frame(11 * step))

    def test_timebase_is_not_hardcoded(self):
        # factor=1：时间戳直接就是纳秒
        _, reports = frames([16.6667] * 62, factor=1.0)
        self.assertAlmostEqual(reports[0]['fps'], 60.0, places=0)

    def test_constants(self):
        self.assertEqual(kdbg_extract_all(830472984), FRAME_EVENT)
        self.assertAlmostEqual(MOVIE_FRAME_COST, 1 / 24)
        self.assertEqual(NANO_SECOND, 1e9)


class TestKperfDataRecords(unittest.TestCase):
    """``kperf_data`` 是 cmd_display / start_get_fps 的事件来源。"""

    RECORD = struct.Struct('<QLLQQQQLLQ')

    def record(self, timestamp, debug_id):
        return self.RECORD.pack(timestamp, 0, 0, 0, 0, 0, 7, debug_id, 0, 0)

    def test_layout(self):
        # [0] 是 mach 时间戳，[7] 是 debug_id —— cmd_display 靠这两个下标
        rows = kperf_data(self.record(1234, 830472984))
        self.assertEqual(rows[0][0], 1234)
        self.assertEqual(rows[0][7], 830472984)

    def test_truncated_tail_drops_only_the_tail(self):
        """回归：旧实现长度不是 64 的倍数时整块丢弃，一包帧全没了。"""
        payload = self.record(1, 830472984) * 3 + b'\x01\x02'
        rows = kperf_data(payload)
        self.assertEqual([row[0] for row in rows], [1, 1, 1])

    def test_empty(self):
        self.assertEqual(kperf_data(b''), [])


if __name__ == '__main__':
    unittest.main()

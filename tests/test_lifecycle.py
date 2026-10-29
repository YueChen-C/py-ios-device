"""Unit tests for :mod:`ios_device.util.lifecycle`.

These tests are pure: they build synthetic ``kdebug`` events instead of talking to
a device, so they can run anywhere.  They cover the launch sequences modelled by
``com.apple.dt.app-life-cycle.dtac`` plus the capture failures the decoder has to
survive (events received out of order, a truncated capture, a capture that starts
in the middle of a launch).
"""
import io
import logging
import unittest
from contextlib import redirect_stdout
from collections import namedtuple

from ios_device.util.lifecycle import (
    AppLifeCycle, AppLifeEvent, AppLifeInterval, Kind, Period, SubState,
    format_duration, convertTime,
)

# Mirrors the attributes KdBufParser exposes that the modeler relies on.
FakeEvent = namedtuple(
    'FakeEvent',
    ['class_code', 'subclass_code', 'final_code', 'func_code', 'args', 'timestamp', 'tid', 'debug_id'],
)

PROCESS_KEY = (4242, 'DemoApp')


def setUpModule():
    # The decoder logs every anomaly it recovers from; keep the test output clean.
    logging.getLogger('Instrument').setLevel(logging.CRITICAL)


def kd(cls, sub, code, func=0, arg0=None, at=0):
    """Build a fake kdebug event (and the debug_id it would have come from)."""
    debug_id = (cls << 24) | (sub << 16) | (code << 2) | func
    args = (arg0, 0, 0, 0) if arg0 is not None else (0, 0, 0, 0)
    return FakeEvent(cls, sub, code & 0x3fff, func, args, at, 7, debug_id)


# -- lifecycle building blocks ------------------------------------------------
EXEC = (0x07, 0x00, 2)
DYLD_START = (0x1f, 0x07, 13)
DYLD_END = (0x1f, 0x07, 1, 2)
BEFORE_MAIN = (0x2b, 0xdc, 4, 0, 10)
APPKIT_START = (0x2b, 0xd8, 1, 0)
APPKIT_INIT_END = (0x2b, 0xd8, 12, 0)
APPKIT_WILL_FINISH_START = (0x2b, 0xd8, 10, 1)
APPKIT_WILL_FINISH_END = (0x2b, 0xd8, 10, 2)
APPKIT_DID_FINISH_START = (0x2b, 0xd8, 11, 1)
APPKIT_DID_FINISH_END = (0x2b, 0xd8, 11, 2)
UIKIT_START = (0x2b, 0x87, 90, 0, 0x32)
UIKIT_SCENE_START = (0x2b, 0x87, 21)
UIKIT_WILL_FINISH_START = (0x2b, 0x87, 23)
UIKIT_WILL_FINISH_END = (0x2b, 0x87, 24)
UIKIT_DID_FINISH_START = (0x2b, 0x87, 25)
UIKIT_DID_FINISH_END = (0x2b, 0x87, 26)
UIKIT_INITIAL_FRAME = (0x2b, 0x87, 12)
LAUNCH_FINISHED = (0x31, 0xca, 1, 2)


def event(signature, at):
    return kd(*signature, at=at)


def uikit_launch():
    """A complete UIKit launch, in the order a healthy capture delivers it."""
    return [
        event(EXEC, 1000),
        event(DYLD_START, 2000),
        event(BEFORE_MAIN, 2500),
        event(DYLD_END, 3000),
        event(UIKIT_START, 4000),
        event(UIKIT_SCENE_START, 5000),
        event(UIKIT_WILL_FINISH_START, 6000),
        event(UIKIT_WILL_FINISH_END, 7000),
        event(UIKIT_DID_FINISH_START, 8000),
        event(UIKIT_DID_FINISH_END, 9000),
        event(UIKIT_INITIAL_FRAME, 10000),
        event(LAUNCH_FINISHED, 20000),
    ]


class _Base(unittest.TestCase):
    def build(self, events, key=PROCESS_KEY):
        """Feed events and return the modeler (the base timebase is ns == ticks)."""
        lifecycle = AppLifeCycle((0, 1, 1), 0)
        for item in events:
            lifecycle.decode_app_lifecycle(item, key)
        return lifecycle

    def rows(self, events, key=PROCESS_KEY):
        return self.build(events, key).finish()

    def assert_phases(self, rows, expected):
        self.assertEqual([(row.period, row.sub_state) for row in rows], expected)

    def render(self, lifecycle, **kwargs):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            lifecycle.format_str(**kwargs)
        return buffer.getvalue()


class TestUIKitLaunch(_Base):

    def test_full_launch_waterfall(self):
        rows = self.rows(uikit_launch())
        self.assert_phases(rows, [
            (Period.EXEC, SubState.PROCESS_EXEC),
            (Period.INITIALIZING, SubState.SYSTEM_INTERFACE_INIT),
            (Period.INITIALIZING, SubState.STATIC_RUNTIME_INIT),
            (Period.LAUNCHING, SubState.UIKIT_INIT),
            (Period.LAUNCHING, SubState.UIKIT_SCENE),
            (Period.LAUNCHING, SubState.UIKIT_WILL_FINISH),
            (Period.LAUNCHING, SubState.UIKIT_SCENE),
            (Period.LAUNCHING, SubState.UIKIT_DID_FINISH),
            (Period.LAUNCHING, SubState.UIKIT_SCENE),
            (Period.LAUNCHING, SubState.INITIAL_FRAME),
        ])
        self.assertTrue(all(row.closed for row in rows))
        # Exec is inferred to end when dyld starts; the -1 tick offsets keep the
        # neighbouring Launching intervals disjoint.
        self.assertEqual(rows[0].duration, 1000)
        self.assertEqual(rows[1].duration, 499)
        self.assertEqual(rows[2].duration, 500)
        self.assertEqual(rows[3].duration, 999)
        self.assertEqual(rows[5].duration, 999)
        self.assertEqual(rows[-1].duration, 10000)
        self.assertEqual(self.build(uikit_launch()).warnings, [])

    def test_completion_event_is_reported(self):
        lifecycle = self.build(uikit_launch()[:-1])
        self.assertTrue(lifecycle.decode_app_lifecycle(event(LAUNCH_FINISHED, 20000), PROCESS_KEY))
        self.assertFalse(self.build([]).decode_app_lifecycle(event(LAUNCH_FINISHED, 500), PROCESS_KEY))

    def test_unrelated_events_are_ignored(self):
        lifecycle = self.build([kd(0x40, 0x01, 5, at=10)])
        self.assertEqual(lifecycle.finish(), [])
        self.assertEqual(lifecycle.events, {})

    def test_events_without_timestamp_are_ignored(self):
        lifecycle = self.build([event(UIKIT_START, 0)])
        self.assertEqual(lifecycle.finish(), [])
        self.assertEqual(len(lifecycle.warnings), 1)


class TestCaptureFailures(_Base):

    def test_end_received_before_begin(self):
        """The Initial Frame Rendering END is occasionally seen before its BEGIN."""
        events = uikit_launch()
        events[-1], events[-2] = events[-2], events[-1]
        self.assertEqual(events[-2].final_code, 1)  # LAUNCH_FINISHED first
        rows = self.rows(events)
        frame = [row for row in rows if row.sub_state == SubState.INITIAL_FRAME]
        self.assertEqual(len(frame), 1)
        self.assertEqual((frame[0].begin, frame[0].end, frame[0].duration), (10000, 20000, 10000))
        self.assertTrue(frame[0].closed)

    def test_truncated_capture_still_reports_open_interval(self):
        """No terminal event: the report must not disappear (old code printed nothing)."""
        lifecycle = self.build(uikit_launch()[:-1])
        rows = lifecycle.finish()
        self.assertEqual(rows[-1].sub_state, SubState.INITIAL_FRAME)
        self.assertFalse(rows[-1].closed)
        self.assertIn('(open)', self.render(lifecycle).splitlines()[-2])

    def test_capture_starting_mid_launch_is_not_dropped(self):
        """Regression: the old append gate discarded everything before a seed event."""
        rows = self.rows([event(UIKIT_INITIAL_FRAME, 5000), event(LAUNCH_FINISHED, 6000)])
        self.assert_phases(rows, [(Period.LAUNCHING, SubState.INITIAL_FRAME)])
        self.assertEqual(rows[0].duration, 1000)
        lifecycle = self.build([event(UIKIT_INITIAL_FRAME, 5000)])
        self.assertTrue(any('launch detector' in warning for warning in lifecycle.warnings))

    def test_missing_end_is_healed_at_next_begin(self):
        lifecycle = AppLifeCycle((0, 1, 1), 0)
        for sub_state, at in ((SubState.UIKIT_INIT, 1000), (SubState.UIKIT_SCENE, 2000)):
            lifecycle.update_app_period(
                AppLifeEvent(Period.LAUNCHING, sub_state, at, PROCESS_KEY, Kind.BEGIN, 0))
        rows = lifecycle.finish()
        self.assert_phases(rows, [(Period.LAUNCHING, SubState.UIKIT_INIT),
                                  (Period.LAUNCHING, SubState.UIKIT_SCENE)])
        self.assertEqual(rows[0].duration, 1000)  # closed at the next BEGIN
        self.assertTrue(any('missing END' in warning for warning in lifecycle.warnings))

    def test_duplicate_begin_is_ignored(self):
        lifecycle = self.build([event(UIKIT_START, 1000), event(UIKIT_START, 1500),
                                event(UIKIT_SCENE_START, 2000)])
        rows = lifecycle.finish()
        self.assertEqual(len(rows), 2)
        self.assertTrue(any('duplicate BEGIN' in warning for warning in lifecycle.warnings))

    def test_unmatched_end_is_dropped(self):
        lifecycle = AppLifeCycle((0, 1, 1), 0)
        lifecycle.update_app_period(
            AppLifeEvent(Period.LAUNCHING, SubState.INITIAL_FRAME, 1000, PROCESS_KEY, Kind.END, 0))
        self.assertEqual(lifecycle.finish(), [])
        self.assertTrue(any('without a matching BEGIN' in warning for warning in lifecycle.warnings))

    def test_dyld_end_double_end_is_not_an_anomaly(self):
        """dyld-init-end asserts two END facts; only the open one may close."""
        lifecycle = self.build([event(DYLD_START, 1000), event(DYLD_END, 2000)])
        rows = lifecycle.finish()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].duration, 1000)
        self.assertEqual(lifecycle.warnings, [])

    def test_processes_are_modelled_independently(self):
        lifecycle = AppLifeCycle((0, 1, 1), 0)
        for item in uikit_launch():
            lifecycle.decode_app_lifecycle(item, PROCESS_KEY)
        for item in [event(UIKIT_START, 1000), event(LAUNCH_FINISHED, 2000)]:
            lifecycle.decode_app_lifecycle(item, (99, 'Other'))
        self.assertEqual(len({row.thread for row in lifecycle.finish()}), 2)


class TestAppKitLaunch(_Base):

    def test_appkit_launch_reaches_initial_frame(self):
        rows = self.rows([
            event(APPKIT_START, 1000),
            event(APPKIT_INIT_END, 2000),
            event(APPKIT_WILL_FINISH_START, 3000),
            event(APPKIT_WILL_FINISH_END, 4000),
            event(APPKIT_DID_FINISH_START, 5000),
            event(APPKIT_DID_FINISH_END, 6000),
            event(LAUNCH_FINISHED, 7000),
        ])
        self.assert_phases(rows, [
            (Period.LAUNCHING, SubState.APPKIT_INIT),
            (Period.LAUNCHING, SubState.APPKIT_SCENE),
            (Period.LAUNCHING, SubState.APPKIT_WILL_FINISH),
            (Period.LAUNCHING, SubState.APPKIT_SCENE),
            (Period.LAUNCHING, SubState.APPKIT_DID_FINISH),
            (Period.LAUNCHING, SubState.INITIAL_FRAME),
        ])
        self.assertTrue(all(row.closed for row in rows))

    def test_marzipan_keeps_launching_period(self):
        rows = self.rows([
            event(UIKIT_START, 1000),
            event(APPKIT_START, 2000),
            event(UIKIT_SCENE_START, 3000),
            event(APPKIT_DID_FINISH_END, 4000),
            event(LAUNCH_FINISHED, 5000),
        ])
        # end-period matches on the *period*, so the Marzipan finish closes the
        # open "Launching" interval (UIKit Scene Creation) and keeps its label.
        self.assert_phases(rows, [
            (Period.LAUNCHING, SubState.UIKIT_INIT),
            (Period.LAUNCHING, SubState.APPKIT_INIT),
            (Period.LAUNCHING, SubState.UIKIT_SCENE),
            (Period.LAUNCHING, SubState.APPKIT_SCENE),
        ])
        self.assertTrue(all(row.period == Period.LAUNCHING for row in rows))

    def test_ui_kind_is_tracked_per_process(self):
        lifecycle = AppLifeCycle((0, 1, 1), 0)
        lifecycle.decode_app_lifecycle(event(UIKIT_START, 1000), (1, 'uikit'))
        lifecycle.decode_app_lifecycle(event(APPKIT_START, 1000), (2, 'appkit'))
        # For a UIKIT process the AppKit finish rule must not match; the old
        # implementation kept one global UI kind and mixed the two apps up.
        self.assertFalse(lifecycle.decode_app_lifecycle(event(APPKIT_DID_FINISH_END, 2000), (1, 'uikit')))
        phases = {}
        for row in lifecycle.finish():
            phases.setdefault(row.thread, []).append(row.sub_state)
        self.assertEqual(phases[(1, 'uikit')], [SubState.UIKIT_INIT])
        self.assertEqual(phases[(2, 'appkit')], [SubState.APPKIT_INIT])


class TestExecInterval(_Base):

    def test_exec_is_closed_by_the_next_begin(self):
        rows = self.rows([event(EXEC, 1000), event(DYLD_START, 5000)])
        self.assertEqual(rows[0].period, Period.EXEC)
        self.assertEqual(rows[0].duration, 4000)
        self.assertTrue(rows[0].closed)


class TestReporting(_Base):

    def test_format_str_prints_and_clears(self):
        lifecycle = self.build(uikit_launch())
        text = self.render(lifecycle)
        lines = text.strip().splitlines()
        self.assertEqual(len(lines), 11)  # 10 phases + summary
        self.assertTrue(lines[-1].startswith('App Thread Process ID:4242 Name:DemoApp,'))
        self.assertIn('19.00 us', lines[-1])  # 20000 - 1000 ticks
        self.assertIn('Launching-Initial Frame Rendering', text)
        self.assertEqual(lifecycle.finish(), [])
        self.assertEqual(self.render(lifecycle), '')

    def test_pid_key_survives_a_late_process_name(self):
        """Keying on (pid, name) split one launch when the name arrived later."""
        lifecycle = AppLifeCycle((0, 1, 1), 0)
        for item in uikit_launch():
            lifecycle.decode_app_lifecycle(item, 4242)
        text = self.render(lifecycle, describe=lambda pid: 'DemoApp' if pid == 4242 else None)
        self.assertEqual(len([line for line in text.splitlines() if 'App Thread' in line]), 1)
        self.assertIn('App Thread Process ID:4242 Name:DemoApp,', text)

    def test_finish_is_idempotent(self):
        lifecycle = self.build(uikit_launch())
        self.assertEqual(lifecycle.finish(), lifecycle.finish())

    def test_wall_time_uses_epoch_anchor(self):
        lifecycle = AppLifeCycle((1000, 1, 1), 1_700_000_000_000_000)
        self.assertEqual(lifecycle.wall_time().timestamp(), 1_700_000_000.0)
        self.assertEqual(lifecycle.wall_time(1000 + 2_000_000_000).timestamp(), 1_700_000_002.0)
        self.assertIsNone(AppLifeCycle((1000, 1, 1), 0).wall_time(2000))

    def test_interval_is_a_named_tuple(self):
        row = self.rows(uikit_launch())[0]
        self.assertIsInstance(row, AppLifeInterval)
        self.assertEqual(row.thread, PROCESS_KEY)


class TestTimeHelpers(unittest.TestCase):

    def test_format_duration_units(self):
        self.assertEqual(format_duration(0), '0.00 ns')
        self.assertEqual(format_duration(1), '1.00 ns')
        self.assertEqual(format_duration(999), '999.00 ns')
        self.assertEqual(format_duration(999_999), '1.00 ms')  # old helper printed 1000.00 us
        self.assertEqual(format_duration(1_500_000), '1.50 ms')
        self.assertEqual(format_duration(2_000_000_000), '2.00 s')
        self.assertEqual(convertTime(1500), '1.50 us')

    def test_negative_durations_do_not_raise(self):
        self.assertEqual(format_duration(-1500), '-1.50 us')

    def test_timebase_conversion_is_exact(self):
        # 24 MHz timebase: 1 tick == 125/3 ns.
        lifecycle = AppLifeCycle((1000, 125, 3), 0)
        self.assertEqual(lifecycle.format_timestamp(1001), 41)
        self.assertEqual(lifecycle.format_timestamp(1000), 0)

    def test_invalid_timebase_falls_back_to_ticks(self):
        lifecycle = AppLifeCycle((0, 0, 0), 0)
        self.assertEqual((lifecycle.numer, lifecycle.denom), (1, 1))
        self.assertEqual(lifecycle.format_timestamp(10), 10)

    def test_malformed_timebase_falls_back_to_ticks(self):
        for bad in (None, [], (1, 2), 'nope'):
            lifecycle = AppLifeCycle(bad, 0)
            self.assertEqual((lifecycle.numer, lifecycle.denom), (1, 1))
            self.assertEqual(lifecycle.format_timestamp(10), 10)


if __name__ == '__main__':
    unittest.main()

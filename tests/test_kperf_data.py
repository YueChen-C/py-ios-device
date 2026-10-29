"""Unit tests for :mod:`ios_device.util.kperf_data`.

Pure tests: synthetic kd_buf / ktrace-v3 byte streams, no device required.
They pin the behaviours that were broken: v3 raw-event chunks were decoded from
the outer stream instead of the chunk payload, THREADNAME events wrote to a
misspelt dict, and ``str(event)`` raised ``TypeError``.
"""
import logging
import struct
import unittest

from ios_device.util.kperf_data import (
    KdBufParser, KperfData,
    KD_BUF_FORMAT, VERSION3_FLAG, V3_RAW_EVENTS, V3_THREAD_MAP,
    kd_header_v3, ktrace_pack,
)

TID = 7
PID = 4242


def read_event(debug_id, timestamp, tid=TID, args=b'\x00' * 32):
    """One 64-byte kd_buf record with raw argument bytes."""
    assert len(args) <= 32
    return struct.pack(KD_BUF_FORMAT, timestamp, args.ljust(32, b'\x00'), tid, debug_id, 0, 0)


def kdebug_id(cls, sub, code, func=0):
    return (cls << 24) | (sub << 16) | (code << 2) | func


def read_event_kd(cls, sub, code, timestamp, func=0, tid=TID, args=b'\x00' * 32):
    return read_event(kdebug_id(cls, sub, code, func), timestamp, tid, args)


def v3_header():
    return kd_header_v3.build(dict(
        tag=0x55AA0300, sub_tag=0, length=0, timebase_numer=125, timebase_denom=3,
        timestamp=0, walltime_secs=0, walltime_usecs=0, timezone_minuteswest=0,
        timezone_dst=0, flags=0))


def v3_thread_map(entries):
    return ktrace_pack.build(dict(
        tag=V3_THREAD_MAP, major=0, minor=0,
        length=32 * len(entries),
        data=[dict(tid=tid, pid=pid, process=name) for tid, pid, name in entries]))


def v3_raw_events(records):
    """Raw-events chunk: 8 zero bytes of preamble, then 64-byte kd_buf records."""
    payload = b'\x00' * 8 + records
    return ktrace_pack.build(dict(tag=V3_RAW_EVENTS, major=0, minor=0,
                                  length=len(payload), data=payload))


def setUpModule():
    # Keep the expected "truncated record" warning out of the test output.
    logging.getLogger('DTXMsg').setLevel(logging.ERROR)


class TestKtraceV3(unittest.TestCase):

    def test_header_magic(self):
        self.assertEqual(v3_header()[:4], VERSION3_FLAG)

    def test_raw_events_are_decoded_from_the_chunk_payload(self):
        stream = (v3_header()
                  + v3_thread_map([(TID, PID, 'DemoApp')])
                  + v3_raw_events(read_event_kd(0x1f, 0x07, 13, 2000)
                                  + read_event_kd(0x31, 0xca, 1, 9000, func=2)))
        kperf = KperfData({})
        events = list(kperf.parse(stream))
        self.assertEqual([event.timestamp for event in events], [2000, 9000])
        self.assertEqual([event.class_code for event in events], [0x1f, 0x31])
        self.assertTrue(all(event.tid == TID for event in events))
        # The preceding thread-map chunk must have populated the pid/name maps.
        self.assertEqual(kperf.threads_pids[TID], PID)
        self.assertEqual(kperf.tid_names[TID], 'DemoApp')

    def test_multiple_raw_event_chunks_are_concatenated(self):
        stream = (v3_header()
                  + v3_raw_events(read_event_kd(0x1f, 0x07, 13, 2000))
                  + v3_raw_events(read_event_kd(0x2b, 0x87, 12, 5000)))
        events = list(KperfData({}).parse(stream))
        self.assertEqual([event.timestamp for event in events], [2000, 5000])

    def test_empty_raw_events_chunk(self):
        stream = v3_header() + v3_raw_events(b'')
        self.assertEqual(list(KperfData({}).parse(stream)), [])


class TestTraceStringHandlers(unittest.TestCase):

    def test_thread_name_does_not_overwrite_the_process_name(self):
        name = b'com.apple.main-thread'
        record = read_event(kdebug_id(0x07, 0x01, 0x04), 1000, args=name)
        kperf = KperfData({})
        kperf.tid_names[TID] = 'DemoApp'
        list(kperf.parse(record))
        self.assertEqual(kperf.thread_names[TID], name.decode())
        self.assertEqual(kperf.tid_names[TID], 'DemoApp')

    def test_new_thread_string_sets_both_maps(self):
        record = read_event(kdebug_id(0x07, 0x01, 0x01), 1000, args=b'MobileSMS')
        kperf = KperfData({})
        list(kperf.parse(record))
        self.assertEqual(kperf.tid_names[TID], 'MobileSMS')
        self.assertEqual(kperf.threads_tids[TID], TID)

    def test_exec_record_updates_the_thread_pid_map(self):
        # TRACE_DATA_EXEC carries the pid in arg1 and is what makes the lifecycle
        # pid filter work.
        record = read_event(kdebug_id(0x07, 0x00, 0x02), 1000,
                            args=struct.pack('<QQQQ', PID, 0, 0, 0))
        kperf = KperfData({})
        events = list(kperf.parse(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(kperf.threads_pids[TID], PID)


class TestKdBufDecoding(unittest.TestCase):

    def test_str_is_usable(self):
        kperf = KperfData({})
        event = list(kperf.parse(read_event_kd(0x1f, 0x07, 13, 2000)))[0]
        self.assertIsInstance(event, KdBufParser)
        self.assertIn('timestamp=2000', str(event))
        self.assertIn('class=0x1f', str(event))

    def test_truncated_tail_is_dropped_with_a_warning(self):
        payload = read_event_kd(0x1f, 0x07, 13, 2000) + b'\x01\x02\x03'
        kperf = KperfData({})
        with self.assertLogs('DTXMsg', level='WARNING') as logs:
            events = list(kperf.parse(payload))
        self.assertEqual(len(events), 1)
        self.assertTrue(any('truncated' in message for message in logs.output))

    def test_v2_header_is_still_supported(self):
        from ios_device.util.kperf_data import VERSION2_FLAG, kd_header_v2
        header = kd_header_v2.build(dict(
            tag=0x55AA0200, number_of_treads=1, is_64bit=1, tick_frequency=24000000,
            threadmap=[dict(tid=TID, pid=PID, process='DemoApp')], _pad=[]))
        payload = header + read_event_kd(0x1f, 0x07, 13, 2000)
        kperf = KperfData({})
        events = list(kperf.parse(payload))
        self.assertEqual(len(events), 1)
        self.assertEqual(kperf.threads_pids[TID], PID)
        self.assertEqual(kperf.tid_names[TID], 'DemoApp')


if __name__ == '__main__':
    unittest.main()

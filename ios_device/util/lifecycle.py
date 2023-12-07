import math
from collections import namedtuple, defaultdict

from ios_device.util.kperf_data import KdBufParser

AppLifeEvent = namedtuple('AppLifeEvent', ['period', 'sub_state', 'time', 'thread', 'kind', 'code'])


def convertTime(data):
    lst = ['ns', 'us', 'ms']
    i = 0
    if data:
        i = int(math.floor(
            math.log(data, 1000)
        ))
    if i >= len(lst):
        i = len(lst) - 1
    return ('%.2f' + " " + lst[i]) % (data / math.pow(1000, i))


class AppLifeCycle:

    def __init__(self, machTimeInfo, usecs_since_epoch):
        self.mach_absolute_time = machTimeInfo[0]
        self.numer = machTimeInfo[1]
        self.denom = machTimeInfo[2]
        self.usecs_since_epoch = usecs_since_epoch
        self.events = defaultdict(list)
        self.process = None
        self.main_ui_thread = None

    def app_launching(self, process):
        self.process = process

    def update_app_period(self, data: AppLifeEvent):
        if self.events[data.thread]:
            self.events[data.thread].append(data)

    def update_start_period(self, data):
        self.events[data.thread].append(data)

    def format_timestamp(self, timestamp):
        return ((timestamp - self.mach_absolute_time) * self.numer) / self.denom

    def format_str(self):
        _tmp_sub_state = {}
        for key, events in self.events.items():
            finish = False
            # 兼容有些 App 先收到 Initial Frame Rendering 的 END，然后再收到 BEIGIN 的问题
            for event in events:
                if event.sub_state == 'Initial Frame Rendering' and event.kind == 'BEGIN':
                    finish = True
            if len(events) == 0:
                continue
            last_event = events[-1]
            if events and last_event.sub_state == 'Initial Frame Rendering' and last_event.kind == 'END' and finish:
                for index, val in enumerate(events):
                    if val.kind == 'BEGIN':
                        _tmp_sub_state[val.sub_state] = self.format_timestamp(val.time)
                    elif val.kind == 'END':
                        if val.sub_state in _tmp_sub_state:
                            end_time = self.format_timestamp(val.time)
                            _tmp_time = end_time - _tmp_sub_state[val.sub_state]
                            print(f'{convertTime(_tmp_time):>10}   {val.period}-{val.sub_state}')
                            del _tmp_sub_state[val.sub_state]
                        else:
                            end_time = self.format_timestamp(val.time)
                            _tmp_time = end_time - self.format_timestamp(events[index-1].time)
                            print(f'{convertTime(_tmp_time):>10} {val.period}-{val.sub_state}')

                total_time = self.format_timestamp(events[-1].time) - self.format_timestamp(events[0].time)
                print(f'App Thread Process ID:{key[0]} Name:{key[1]}, Process Total Time:{convertTime(total_time)}')
                self.events[key].clear()

    def decode_app_lifecycle(self, event: KdBufParser, thread):
        if event.class_code == 0x1f:  # dyld-init
            if event.subclass_code == 0x7 and event.final_code == 13:
                self.update_start_period(AppLifeEvent('Initializing',
                                                      'System Interface Initialization (Dyld init)', event.timestamp,
                                                      thread, 'BEGIN',
                                                      event.debug_id))
            elif event.subclass_code == 0x7 and event.final_code == 1 and event.func_code == 2:
                self.update_app_period(AppLifeEvent('Initializing',
                                                    'Static Runtime Initialization', event.timestamp, thread, 'END',
                                                    event.debug_id))

        elif event.class_code == 0x31 and event.subclass_code == 0xca and event.final_code == 1 and event.func_code == 2:  # AppKit/UIKit common application launch phases
            self.update_app_period(AppLifeEvent('Launching',
                                                'Initial Frame Rendering', event.timestamp, thread, 'END',
                                                event.debug_id))

        elif event.class_code == 0x2b:
            if event.subclass_code == 0xd8:  # appkit-init
                if event.final_code == 1 and event.func_code == 0:
                    if not self.main_ui_thread:
                        self.update_app_period(AppLifeEvent('Launching',
                                                            'AppKit Initialization', event.timestamp, thread,
                                                            'BEGIN', event.debug_id))
                        self.main_ui_thread = 'UIKIT'
                    elif self.main_ui_thread == 'UIKIT':
                        self.update_app_period(AppLifeEvent('Launching',
                                                            'UIKit Initialization', event.timestamp, thread, 'END',
                                                            event.debug_id))
                        self.update_app_period(AppLifeEvent('Launching',
                                                            'AppKit Initialization', event.timestamp, thread, 'BEGIN',
                                                            event.debug_id))
                        self.main_ui_thread = 'MARZIPAN'

                elif event.final_code == 12 and event.func_code == 0:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'AppKit Initialization', event.timestamp, thread, 'END',
                                                        event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'AppKit Scene Creation', event.timestamp, thread, 'BEGIN',
                                                        event.debug_id))
                elif event.final_code == 12 and event.func_code == 1:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'AppKit Scene Creation', event.timestamp, thread, 'END',
                                                        event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'applicationWillFinishLaunching()', event.timestamp, thread,
                                                        'BEGIN', event.debug_id))
                elif event.final_code == 12 and event.func_code == 2:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'applicationWillFinishLaunching()', event.timestamp, thread,
                                                        'END', event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'AppKit Scene Creation', event.timestamp, thread, 'BEGIN',
                                                        event.debug_id))
                elif event.final_code == 11 and event.func_code == 1:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'AppKit Scene Creation', event.timestamp, thread, 'END',
                                                        event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'applicationDidFinishLaunching()', event.timestamp, thread,
                                                        'BEGIN', event.debug_id))

                elif event.final_code == 11 and event.func_code == 2:
                    if self.main_ui_thread == 'APPKIT':
                        self.update_app_period(AppLifeEvent('Launching',
                                                            'applicationDidFinishLaunching()', event.timestamp, thread,
                                                            'END', event.debug_id))
                        self.update_app_period(AppLifeEvent('Launching',
                                                            'Initial Frame Rendering', event.timestamp, thread, 'BEGIN',
                                                            event.debug_id))
                    elif self.main_ui_thread == 'MARZIPAN':
                        self.update_app_period(AppLifeEvent('Launching',
                                                            'applicationDidFinishLaunching()', event.timestamp, thread,
                                                            'END', event.debug_id))
                        self.update_app_period(AppLifeEvent('Launching',
                                                            'AppKit Scene Creation', event.timestamp, thread, 'BEGIN',
                                                            event.debug_id))

            elif event.subclass_code == 0x87:  # UIKit application launch phases
                if event.final_code == 90 and event.args[0] == 0x32:
                    self.update_start_period(AppLifeEvent('Launching',
                                                          'UIKit Initialization', event.timestamp, thread, 'BEGIN',
                                                          event.debug_id))
                    self.main_ui_thread = 'UIKIT'

                elif event.final_code == 21:
                    if self.main_ui_thread == 'UIKIT':
                        self.update_app_period(AppLifeEvent('Launching',
                                                            'UIKit Initialization', event.timestamp, thread, 'END',
                                                            event.debug_id))
                        self.update_app_period(AppLifeEvent('Launching',
                                                            'UIKit Scene Creation', event.timestamp, thread, 'BEGIN',
                                                            event.debug_id))
                    elif self.main_ui_thread == 'MARZIPAN':

                        self.update_app_period(AppLifeEvent('Initializing',
                                                            'AppKit Scene Creation', event.timestamp, thread, 'END',
                                                            event.debug_id))
                        self.update_app_period(AppLifeEvent('Initializing',
                                                            'UIKit Scene Creation', event.timestamp, thread, 'BEGIN',
                                                            event.debug_id))

                elif event.final_code == 23:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'UIKit Scene Creation', event.timestamp, thread, 'END',
                                                        event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'willFinishLaunchingWithOptions()', event.timestamp, thread,
                                                        'BEGIN', event.debug_id))
                elif event.final_code == 24:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'willFinishLaunchingWithOptions()', event.timestamp, thread,
                                                        'END', event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'UIKit Scene Creation', event.timestamp, thread, 'BEGIN',
                                                        event.debug_id))

                elif event.final_code == 25:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'UIKit Scene Creation', event.timestamp, thread, 'END',
                                                        event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'didFinishLaunchingWithOptions()', event.timestamp, thread,
                                                        'BEGIN', event.debug_id))

                elif event.final_code == 26:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'didFinishLaunchingWithOptions()', event.timestamp, thread,
                                                        'END', event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'UIKit Scene Creation', event.timestamp, thread, 'BEGIN',
                                                        event.debug_id))

                elif event.final_code == 300:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'UIKit Scene Creation', event.timestamp, thread, 'END',
                                                        event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'sceneWillConnectTo()', event.timestamp, thread, 'BEGIN',
                                                        event.debug_id))
                elif event.final_code == 301:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'sceneWillConnectTo()', event.timestamp, thread, 'END',
                                                        event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'UIKit Scene Creation', event.timestamp, thread, 'BEGIN',
                                                        event.debug_id))
                elif event.final_code == 312:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'UIKit Scene Creation', event.timestamp, thread, 'END',
                                                        event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'sceneWillEnterForeground()', event.timestamp, thread, 'BEGIN',
                                                        event.debug_id))

                elif event.final_code == 313:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'sceneWillEnterForeground()', event.timestamp, thread, 'END',
                                                        event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'UIKit Scene Creation', event.timestamp, thread, 'BEGIN',
                                                        event.debug_id))

                elif event.final_code == 12:
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'UIKit Scene Creation', event.timestamp, thread, 'END',
                                                        event.debug_id))
                    self.update_app_period(AppLifeEvent('Launching',
                                                        'Initial Frame Rendering', event.timestamp, thread, 'BEGIN',
                                                        event.debug_id))
            elif event.subclass_code == 0xdc:  # appkit-init
                if event.final_code == 4 and event.func_code == 0 and event.args[0] == 10:
                    self.update_app_period(AppLifeEvent('Initializing',
                                                        'System Interface Initialization (Dyld init)', event.timestamp,
                                                        thread,
                                                        'END', event.debug_id))
                    self.update_app_period(AppLifeEvent('Initializing',
                                                        'Static Runtime Initialization', event.timestamp, thread,
                                                        'BEGIN', event.debug_id))

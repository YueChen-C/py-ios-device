import io
import struct
import typing
from copy import deepcopy
from dataclasses import dataclass, field

import execjs


@dataclass
class GRCDecodeOrder:
    """ 解码序列
    """
    key: str
    require: bool
    val: int = field(default=None, repr=True)

    @staticmethod
    def decode(data):
        _list = list()
        for _index in data:
            _list.append(GRCDecodeOrder(*_index))
        return _list


@dataclass
class GRCDisplayOrder:
    """ 最终展示显示编码序列
    """
    display: str
    scale: int
    content: str
    method: str
    mix: int
    min: int

    @staticmethod
    def decode(data):
        _list = list()
        for i in data:
            _list.append(GRCDisplayOrder(*i))
        return _list


@dataclass
class TraceData:
    """ 返回 bytes 数据流
    """
    type: int
    time: int
    time_stamp: int
    trace_num: int  # 组数量，每组根据 GRCDecodeOrder 序列进行相关逻辑解析
    trace_data: bytes
    padding: int = field(default=None, repr=False)  # 未知填充


class GPUTraceData:
    def __init__(self, time):
        self.time = time
        self.data_list = list()

    def append(self, data: GRCDecodeOrder):
        self.data_list.append(data)

    def get_size(self):
        return len(self.data_list)

    def get(self, index):
        return self.data_list[index]


class GPUCounterData:

    def __init__(self, fast_counter_time, last_counter_time):
        self.fast_counter_time = fast_counter_time
        self.last_counter_time = last_counter_time

        self.counter_data_list = list()

    def append(self, data):
        self.counter_data_list.append(data)

    def get(self, index):
        return self.counter_data_list[index]

    def get_size(self):
        return len(self.counter_data_list)


class JSEvn:

    def __init__(self, js_str, display_key_list, decode_key_list, mach_time_factor):
        self.display_key_list = display_key_list  # 显示顺序
        self.decode_key_list = decode_key_list  # 解码顺序
        self.mach_time_factor = mach_time_factor
        self.counter_list = None
        self.long_list = None
        self.fast_counter_time = 0

        js = self.format_js(js_str, display_key_list, decode_key_list)
        self.ctx = execjs.compile(js)

    def trace_decode(self, trace_data: TraceData) -> typing.List[GPUTraceData]:
        """ trace 转换成 Long
        :param trace_data:
        :return:
        """
        index = 0
        data_io = io.BytesIO(trace_data.trace_data)  # 二进制流
        data_list = []
        while True:
            index += 1
            d = data_io.read(8)
            if not d:
                break
            _temp_val_list = []
            tmp_data = GPUTraceData(struct.unpack('Q', d)[0])
            for i in self.decode_key_list:
                d = data_io.read(8)
                i.val = struct.unpack('Q', d)[0]
                tmp_data.append(deepcopy(i))
            data_list.append(tmp_data)
        return data_list

    def get_counter_list(self, trace_data: TraceData) -> typing.List[GPUCounterData]:
        counter_list = list()
        index = 0
        fast_counter = None
        trace_list = self.trace_decode(trace_data)
        while index < len(trace_list):
            _counter = deepcopy(trace_list[index])
            tmp_counter = deepcopy(trace_list[index])
            if index == 0:
                counter_list.append(self._calculation(_counter, _counter))
            else:
                counter_list.append(self._calculation(fast_counter, _counter))
            fast_counter = tmp_counter
            index += 1
        return counter_list

    @staticmethod
    def _calculation(fast_counter: GPUTraceData, last_counter: GPUTraceData) -> GPUCounterData:
        """ 二次处理数据，某些情况需要处理数据差值
        :param fast_counter:
        :param last_counter:
        :return:
        """
        counter_data = GPUCounterData(fast_counter.time, last_counter.time)
        for index, counter in enumerate(last_counter.data_list):
            if not counter.key.startswith('_'):
                counter_data.append(counter)
            else:
                if counter.require:
                    counter_data.append(counter)
                else:
                    counter.val = counter.val - fast_counter.get(index).val
                    counter_data.append(counter)
        return counter_data

    @staticmethod
    def counter_to_js(counter_list: typing.List[GPUCounterData]):
        js_counter_list = []
        for i in counter_list:
            js_counter_list.append(i.last_counter_time)
            for k in i.counter_data_list:
                js_counter_list.append(k.val)
        return js_counter_list

    def ex_js(self, trace_data: TraceData):
        counter_list = self.get_counter_list(trace_data)
        js_val_list = self.counter_to_js(counter_list)
        counter_result = self.ctx.call('EvaluateGPUCounter', len(counter_list), js_val_list)
        return counter_result, counter_list

    def dump_trace(self, trace_data):

        counter_result, counter_list = self.ex_js(trace_data)

        for i, key in enumerate(counter_list):
            if not self.fast_counter_time:
                self.fast_counter_time = key.fast_counter_time
            timestamp = (key.last_counter_time - self.fast_counter_time) * self.mach_time_factor
            timestamp = round(timestamp / 1000000000, 6)
            start = i * len(self.display_key_list)
            for index, k in enumerate(self.display_key_list):
                formatted_data = f'{timestamp:<10}' + f'{k.display:<45}' + f'{round(counter_result[start + index] * k.mix, 2):<6}'
                print(formatted_data)
            print("-----------------------------------------------------------")

    def format_js(self, js_str, display_key_list, decode_key_list):
        stringBuilder = ''

        stringBuilder += js_str

        for i in decode_key_list:
            stringBuilder += f'var {i.key} = 0;\n'
        stringBuilder += f"var MACH_TIME_FACTOR = {self.mach_time_factor};\n"
        stringBuilder += f"var lastTimestamp = 0;\n"
        stringBuilder += f"var MTLStat_nSec = 0;\n"

        stringBuilder += 'function EvaluateGPUCounter(counterNum,counterResult) {\n'
        stringBuilder += 'var _CounterResult = [];\n'
        stringBuilder += 'for (var index = 0; index < counterNum; ++index) {\n'
        stringBuilder += f'var startIndex = index * {len(decode_key_list) + 1} + 1;\n'
        stringBuilder += f'var timestamp = (counterResult[0 + index * {len(decode_key_list) + 1}]) * MACH_TIME_FACTOR;\n'
        stringBuilder += f'MTLStat_nSec = timestamp - lastTimestamp;\n'
        stringBuilder += f'var grcGPUCycles = counterResult[1 + startIndex];\n'
        for index, k in enumerate(decode_key_list):
            stringBuilder += f'{k.key} = counterResult[{index} + startIndex];\n'
            stringBuilder += f'{k.key}_norm = counterResult[{index} + startIndex] / grcGPUCycles\n'

        for i in display_key_list:
            stringBuilder += 'try {' + f'value = {i.method}(); ' + '_CounterResult.push(value);} catch(err) {console.error(err); _CounterResult.push(0);}\n'
        stringBuilder += 'lastTimestamp = timestamp\n'
        stringBuilder += '}\n'
        stringBuilder += 'return _CounterResult\n'
        stringBuilder += '}\n'
        return stringBuilder

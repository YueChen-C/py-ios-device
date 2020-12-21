# py-ios-device

Get IOS performance data through instruments protocol

win，mac 跨平台方案，通过 Instruments 私有协议获取 iOS 相关性能数据。


### 安装:

pip3 install py_ios_device

### 使用方法:
1.创建对象后获取数据:

```
from py_ios_device.py_ios_device import PyiOSDevice
device = PyiOSDevice("device_id")
device.connect()
pr = device.get_processes()
print(pr)
device.disconnect()
```
connect 后持续使用一个管道

2.单次使用
```
from py_ios_device import ios_device
pr = ios_device.get_processes("divece_id")
print(pr)
```

3.异步回调
```
from py_ios_device import ios_device

def c(res):
    print(res)

ios_device.get_network(c)
```

### api

get_network  # 获取网络信息

get_processes  # 获取进程列表

get_performance_by_process_id  # 根据设备中的进程 id 获取性能数据

get_performance_by_app_name  # 根据应用名称获取性能数据

launch_app  # 启动 app

launch_app_callback   # 启动 app 具有回调函数

get_all_process_performance  # 获取所有进程的性能数据

ps: 目前个别接口数据获取有问题,调试ing


### sysmontap.py demo
```
[
    {
        "PerCPUUsage": [
            {
                "CPU_NiceLoad": 0.0,
                "CPU_SystemLoad": -1.0,
                "CPU_TotalLoad": 11.881188118811878,
                "CPU_UserLoad": -1.0
            },
            {
                "CPU_NiceLoad": 0.0,
                "CPU_SystemLoad": -1.0,
                "CPU_TotalLoad": 17.0,
                "CPU_UserLoad": -1.0
            }
        ],
        "EndMachAbsTime": 656566442146,
        "CPUCount": 2,
        "EnabledCPUs": 2,
        "SystemCPUUsage": {
            "CPU_NiceLoad": 0.0,
            "CPU_SystemLoad": -1.0,
            "CPU_TotalLoad": 28.881188118811878,
            "CPU_UserLoad": -1.0
        },
        "Type": 33,
        "StartMachAbsTime": 656542341717
    },
    {
        "Processes": {
            "351": [
                351,            // pid 
                417710325760,   // memVirtualSize
                770048,         // memResidentSize
                0.0,            // cpuUsage
                528,
                -82,            
                934232,         // physFootprint
                819200,         // memAnon
                0.0,            // powerScore
                708608          // diskBytesRead
            ],
            "519": [
                519,
                418581921792,
                46628864,
                13.8574323237612,
                30281,
                6465,
                61965152,
                20381696,
                14.082756426586586,
                57790464
            ],
            "311": [
                311,
                417748434944,
                6635520,
                0.0,
                10189,
                43,
                1671552,
                1540096,
                0.0,
                22274048
            ],
            "271": [
                271,
                417744961536,
                4718592,
                0.0,
                8188,
                473,
                2130344,
                1998848,
                0.0,
                36442112
            ]
        },
        "Type": 5,
        "EndMachAbsTime": 656567535862,
        "StartMachAbsTime": 656542716738
    }
]
```

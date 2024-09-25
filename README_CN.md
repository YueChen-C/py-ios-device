# py-ios-device
[![PyPI](https://img.shields.io/pypi/v/py-ios-device)](https://pypi.org/project/py-ios-device/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/py-ios-device)](https://pypistats.org/search/py-ios-device)

A python based Apple instruments protocol，you can get CPU, Memory and other metrics from real iOS devices

win，mac 跨平台方案，通过 Instruments 私有协议获取 iOS 相关性能指标数据。

相关文章链接:https://testerhome.com/topics/27159

[中文文档](README_CN.md)


[Java 版本](https://github.com/YueChen-C/java-ios-device)


## pip 仓库:
    pip install py-ios-device
    
python 版本: 3.7 +
### instruments 相关功能列表：
- [x] 获取系统的 内存、cpu 数据
- [x] 获取应用的 内存、cpu 数据
- [x] 获取 FPS 数据 <= 60
- [x] 获取 FPS 和卡顿等数据支持 FPS <= 120
- [x] 获取 网络数据
- [x] 设置模拟真机网络状态，例如 2g 、3g、 lost 等
- [x] 设置模拟真机设备高压过热状态
- [x] 事件监听，监听app 启动，退出，后台运行等
- [x] 启动杀死 APP
- [x] 运行 xcuitest 启动 wda
- [x] 导出内核堆栈快照
- [x] 解析内核数据流
- [x] 获取 iOS GPU Counters 
- [x] 设置虚拟位置信息 
- [x] 获取 APP 启动时间
- [x] pull && push 文件


### 其他功能列表
- [x] 描述文件管理 例如：安装 卸载 Fiddler 证书等
- [x] 获取系统日志流
- [x] 获取崩溃日志
- [x] 获取抓包数据转发至 wiershark
- [x] 应用管理:安装、卸载、启动、查询、运行状态等
- [x] 获取电池信息

## 使用文档：

### 支持 iOS 17  (暂时不支持命令行模式)

```bash
pip install pymobiledevice3
sudo python3 -m pymobiledevice3 remote start-tunnel

# 建议使用 go-ios 创建隧道性能更优秀
npm install -g go-ios  
sudo ios tunnel start && ios tunnel start --userspace
curl http://127.0.0.1:60105/tunnels
```

```python
from ios_device.remote.remote_lockdown import RemoteLockdownClient
from ios_device.servers.Instrument import  InstrumentServer
from demo.instrument_demo.sysmontap import  sysmontap

# support ios tunnel start --userspace 无 sudo 启动使用方法
# [{"address":"fd17:cafe:59d4::1","rsdPort":54934,"udid":"00008101-0018242C3XXXXXXXXX","userspaceTun":true,"userspaceTunPort":60106}]

host = 'fd17:cafe:59d4::1'
port = 54934  
with RemoteLockdownClient((host, port), userspace_port=60106) as rsd:
    rpc = InstrumentServer(rsd).init()
    sysmontap(rpc)
    rpc.stop()
```


## pip 仓库:
    > pip install py-ios-device
    > pyidevice --help
    > pyidevice instruments --help


#### 获取设备列表

```bash
$ pyidevice devices
```

#### 获取设备信息

```bash
$ pyidevice  deviceinfo --udid=xxxxxx
```

#### 获取系统性能数据

```bash
$ pyidevice instruments monitor 
Memory  >> {'App Memory': '699.69 MiB', 'Cached Files': '1.48 GiB', 'Compressed': '155.17 MiB', 'Memory Used': '1.42 GiB', 'Wired Memory': '427.91 MiB', 'Swap Used': '46.25 MiB'}
Network >> {'Data Received': '4.07 GiB', 'Data Received/sec': '4.07 GiB', 'Data Sent': '2.54 GiB', 'Data Sent/sec': '2.54 GiB', 'Packets in': 2885929, 'Packets in/sec': 6031576, 'Packets Out': 2885929, 'Packets Out/sec': 2885929}
Disk    >> {'Data Read': '117.91 GiB', 'Data Read/sec': 0, 'Data Written': '64.28 GiB', 'Data Written/sec': 0, 'Reads in': 9734132, 'Reads in/sec': 9734132, 'Writes Out': 6810640, 'Writes Out/sec': 6810640}

$ pyidevice instruments monitor --filter = memory
Memory  >> {'App Memory': '699.69 MiB', 'Cached Files': '1.48 GiB', 'Compressed': '155.17 MiB', 'Memory Used': '1.42 GiB', 'Wired Memory': '427.91 MiB', 'Swap Used': '46.25 MiB'}

```

#### 获取单个应用性能数据
```bash
$ pyidevice instruments appmonitor  -b cn.rongcloud.im
{'Pid': 30897, 'Name': 'SealTalk', 'CPU': '0 %', 'Memory': '35.72 MiB', 'DiskReads': '24.12 MiB', 'DiskWrites': '2.28 MiB', 'Threads': 13}
{'Pid': 30897, 'Name': 'SealTalk', 'CPU': '3.4 %', 'Memory': '35.72 MiB', 'DiskReads': '24.12 MiB', 'DiskWrites': '2.30 MiB', 'Threads': 13}

```

#### 获取自定义返回数据内容的应用性能数据
```bash
$ pyidevice instruments sysmontap --help
$ pyidevice instruments sysmontap  -b com.tencent.xin --proc_filter physFootprint,cpuUsage --processes --sort cpuUsage # 只显示 memVirtualSize,cpuUsage 参数的进程列表，且根据 cpuUsage 字段排序 

[('WeChat', {'cpuUsage': 0.03663705586691998, 'physFootprint': 2179284992, 'name': 'WeChat', 'pid': 99269})]
[('WeChat', {'cpuUsage': 0.036558268613227536, 'physFootprint': 2179284992, 'name': 'WeChat', 'pid': 99269})]

```


#### 获取 FPS 数据 FPS <= 60

```bash
$ pyidevice instruments fps

{'currentTime': '2021-05-11 14:14:40.259059', 'fps': 52}
{'currentTime': '2021-05-11 14:14:40.259059', 'fps': 56}
```

#### 获取 FPS display 数据支持更高的 FPS <= 120

```bash
$ pyidevice instruments display
{'time': 151.28127908706665, 'fps': 10.999274047912838, 'jank': 0, 'big_jank': 0, 'stutter': 0.0}
```


#### 获取 网络数据
```bash
$ pyidevice instruments networking
# 获取全局网络数据
"connection-update{\"RxPackets\": 2, \"RxBytes\": 148, \"TxPackets\": 2, \"TxBytes\": 263, \"RxDups\": 0, \"RxOOO\": 0, \"TxRetx\": 0, \"MinRTT\": 0.05046875, \"AvgRTT\": 0.05046875, \"ConnectionSerial\": 5}"
"connection-update{\"RxPackets\": 4, \"RxBytes\": 150, \"TxPackets\": 3, \"TxBytes\": 1431, \"RxDups\": 0, \"RxOOO\": 0, \"TxRetx\": 0, \"MinRTT\": 0.0539375, \"AvgRTT\": 0.0541875, \"ConnectionSerial\": 4}"

$ pyidevice instruments network_process -p com.tencent.xin 
# 获取单应用网络数据
{403: {'net.packets.delta': 119, 'time': 1620720061.0643349, 'net.tx.bytes': 366715, 'net.bytes.delta': 63721, 'net.rx.packets.delta': 47, 'net.tx.packets': 633, 'net.rx.bytes': 34532, 'net.bytes': 401247, 'net.tx.bytes.delta': 56978, 'net.rx.bytes.delta': 6743, 'net.rx.packets': 169, 'pid': 403, 'net.tx.packets.delta': 72, 'net.packets': 802}}
{403: {'net.packets.delta': 13, 'time': 1620720076.2191892, 'net.tx.bytes': 1303204, 'net.bytes.delta': 5060, 'net.rx.packets.delta': 5, 'net.tx.packets': 2083, 'net.rx.bytes': 46736, 'net.bytes': 1349940, 'net.tx.bytes.delta': 4682, 'net.rx.bytes.delta': 378, 'net.rx.packets': 379, 'pid': 403, 'net.tx.packets.delta': 8, 'net.packets': 2462}}

```

#### 设置设备状态 iOS 版本 > 12
可以模拟网络状态，例如 2g 、3g、 lost 等<br>
可以模拟设备高压过热状态
```bash
$ pyidevice instruments condition get
# 获取设备状态配置信息

$ pyidevice instruments condition set -c SlowNetworkCondition -p SlowNetwork2GUrban
# 模拟网络状态，例如 2g 、3g、 lost 等

$ pyidevice instruments condition set -c ThermalCondition -p ThermalCritical
# 模拟设备高压过热状态下的运行模式
```


#### 监听 app 事件
可以监听所有 app 事件例如： 退到后台，杀死，启动，重启等
```bash
$ pyidevice instruments notifications
[{'execName': 'MobileNotes', 'state_description': 'Foreground Running', 'elevated_state_description': 'Foreground Running', 'displayID': 'com.apple.mobilenotes', 'mach_absolute_time': 27205542653928, 'appName': 'Notes', 'elevated_state': 8, 'timestamp': 1620714619.1264, 'state': 8, 'pid': 99367}]
[{'execName': 'MobileNotes', 'state_description': 'Background Running', 'elevated_state_description': 'Background Running', 'displayID': 'com.apple.mobilenotes', 'mach_absolute_time': 27205678872050, 'appName': 'Notes', 'elevated_state': 4, 'timestamp': 1620714624.802145, 'state': 4, 'pid': 99367}]
[{'execName': 'MobileNotes', 'state_description': 'Background Task Suspended', 'elevated_state_description': 'Background Task Suspended', 'displayID': 'com.apple.mobilenotes', 'mach_absolute_time': 27205683486410, 'appName': 'Notes', 'elevated_state': 2, 'timestamp': 1620714624.99441, 'state': 2, 'pid': 99367}]
```

#### 内核堆栈快照信息
导出内核堆栈快照信息
```bash
$ pyidevice instruments stackshot --out stackshot.log

```

#### 解析 core_profile 内核数据流 
```bash
$ pyidevice instruments instruments core_profile --pid=1107
SealTalk(1107)             PERF_THD_CSwitch (0x25010014)                               DBG_PERF          PERF_DATA                     DBG_FUNC_NONE  
SealTalk(1107)             MACH_DISPATCH (0x1400080)                                   DBG_MACH          DBG_MACH_SCHED                DBG_FUNC_NONE  
SealTalk(1107)             DecrSet (0x1090004)                                         DBG_MACH          DBG_MACH_EXCP_DECI            DBG_FUNC_NONE  

```

#### 获取 Metal GPU Counters
```bash
$ pyidevice instruments gup_counters
15.132907 ALU Limiter                                  93.77 
15.132907 Texture Sample Limiter                       39.62 
15.132907 Texture Write Limiter                        13.87 
15.132907 Buffer Read Limiter                          0.01  
15.132907 Buffer Write Limiter                         0     
15.132907 Threadgroup/Imageblock Load Limiter          17.16 
15.132907 Threadgroup/Imageblock Store Limiter         10.9  
15.132907 Fragment Input Interpolation Limiter         15.74 
15.132907 GPU Last Level Cache Limiter                 6.24  
15.132907 Vertex Occupancy                             0     
15.132907 Fragment Occupancy                           91.44 
15.132907 Compute Occupancy                            0     
15.132907 GPU Read Bandwidth                           2.65  
15.132907 GPU Write Bandwidth                          1.25  
```

#### 获取 App 启动时间以及生命周期
```bash
$ pyidevice instruments app_lifecycle -b cn.rongcloud.im
  31.20 ms   Initializing-System Interface Initialization (Dyld init)
  14.33 ms   Initializing-Static Runtime Initialization
  35.68 ms   Launching-UIKit Initialization
 810.46 us   Launching-UIKit Scene Creation
 100.64 ms   Launching-didFinishLaunchingWithOptions()
   2.91 ms   Launching-UIKit Scene Creation
  21.85 ms   Launching-Initial Frame Rendering
App Thread Process ID:6506076, Total Time:207.41 ms
```

### 其他功能示例
#### 描述文件管理 

描述文件管理 例如：安装 卸载 Fiddler，Charles 证书等

```bash
$ pyidevice profiles list
{
    "OrderedIdentifiers": [
        "aaaff7e2b7df39eeb77bfbc0cd7a70ea99f3fd97a"
    ],
    "ProfileManifest": {
        "aaaff7e2b7df39eeb77bfbc0cd7a70ea99f3fd97a": {
            "Description": "DO_NOT_TRUST_FiddlerRoot",
            "IsActive": true
        }
    },
    "ProfileMetadata": {
        "aaaff7e2b7df39eeb77bfbc0cd7a70ea99f3fd97a": {
            "PayloadDisplayName": "DO_NOT_TRUST_FiddlerRoot",
            "PayloadRemovalDisallowed": false,
            "PayloadUUID": "C8CE7BC1-F840-4616-B606-337F8CB6AE19",
            "PayloadVersion": 1
        }
    },
    "Status": "Acknowledged"
}

$ pyidevice profiles install  --path Downloads/charles-certificate.pem
## 安装 charles 证书

$ pyidevice profiles remove --name fe7371d9ce36c541ac8dee5f51f3b490b2aa98dcd95699ee44717fd5233fe7a0a
## 删除 charles 证书
```

#### 获取日志流数据
```bash
$ pyidevice syslog
# --path
# --filter
# 获取 日志流
```


#### 获取 crash 日志数据

```bash
$ pyidevice crash list
# 获取 crash日志列表
['.', '..', 'com.apple.appstored', 'JetsamEvent-2021-05-12-112126.ips']

$ pyidevice crash export --name JetsamEvent-2021-05-12-112126.ips
# 导出 crash 日志

$ pyidevice crash delete --name JetsamEvent-2021-05-12-112126.ips
# 删除 crash 日志

$ pyidevice crash shell
# 进入命令行操作模式

```


#### 应用管理
应用管理:安装、卸载、启动、查询、运行状态等
```bash
$ pyidevice apps list

$ pyidevice apps install --ipa_path

$ pyidevice apps uninstall --bundle_id 

$ pyidevice apps launch --bundle_id

$ pyidevice apps kill --bundle_id

$ pyidevice apps shell 

```

#### 抓包数据
```bash
$ pyidevice pcapd ./test/test.pacp
# 抓包保存数据

$ pyidevice pcapd - | "/Applications/Wireshark.app/Contents/MacOS/Wireshark" -k -i -
# mac 转发至 Wireshark

$ pyidevice pcapd - | "D:\Program Files\Wireshark\Wireshark.exe" -k -i -
# win 转发至 Wireshark

```

#### 获取电池信息
```bash
$ pyidevice battery
# [Battery] time=1622777708, current=-71, voltage=4330, power=-307.43, temperature=3279

```

#### 开启开发者模式
```bash
$ pyidevice enable_developer_mode
```


#### using python api
```python

from ios_device.cli.base import InstrumentsBase
from ios_device.util.dtx_msg import DTXMessage

with InstrumentsBase() as rpc:
    def sysmontap_callback(res: DTXMessage):
        print(res.selector, res.auxiliaries)

    rpc.process_attributes = ['name', 'pid']
    rpc.system_attributes = rpc.device_info.sysmonSystemAttributes()
    rpc.sysmontap(sysmontap_callback)


```


QQ 交流群：37042417


使用文档: [查看文档](./doc/使用文档.md)
使用demo: [查看demo](./test/test.py)


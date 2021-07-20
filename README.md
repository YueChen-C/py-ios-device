# py-ios-device
[![PyPI](https://img.shields.io/pypi/v/py-ios-device)](https://pypi.org/project/py-ios-device/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/py-ios-device)](https://pypistats.org/search/py-ios-device)

A python based Apple instruments protocol，you can get CPU, Memory and other metrics from real iOS devices

win，mac 跨平台方案，通过 Instruments 私有协议获取 iOS 相关性能指标数据。

相关文章链接:https://testerhome.com/topics/27159

[English](README_EN.md)


[Java 版本](https://github.com/YueChen-C/java-ios-device)


## pip 仓库:
    pip install py-ios-device
    
python 版本: 3.7 +
### instruments 相关功能列表：
- [x] 获取 内存、cpu 数据
- [x] 获取 FPS 数据
- [x] 获取 网络数据
- [x] 设置模拟真机网络状态，例如 2g 、3g、 lost 等
- [x] 设置模拟真机设备高压过热状态
- [x] 事件监听，监听app 启动，退出，后台运行等
- [x] 启动杀死 APP
- [x] 运行 xcuitest 启动 wda
- [x] 导出内核堆栈快照
- [ ] 解析内核数据流


### 其他功能列表
- [x] 描述文件管理 例如：安装 卸载 Fiddler 证书等
- [x] 获取系统日志流
- [x] 获取崩溃日志
- [x] 获取抓包数据转发至 wiershark
- [x] 应用管理:安装、卸载、启动、查询、运行状态等
- [x] 获取电池信息
- [ ] 截图
- [ ] 打开 wifi 连接模式

## 命令行使用文档：

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
$ pyidevice --udid=xxxxxx deviceinfo
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

#### 获取应用性能数据

```bash
$ pyidevice instruments sysmontap --help
$ pyidevice instruments sysmontap  -b com.tencent.xin --proc_filter memVirtualSize,cpuUsage --processes --sort cpuUsage # 只显示 memVirtualSize,cpuUsage 参数的进程列表，且根据 cpuUsage 字段排序 

[('WeChat', {'cpuUsage': 0.03663705586691998, 'memVirtualSize': 2179284992, 'name': 'WeChat', 'pid': 99269})]
[('WeChat', {'cpuUsage': 0.036558268613227536, 'memVirtualSize': 2179284992, 'name': 'WeChat', 'pid': 99269})]

```


#### 获取 FPS 数据

```bash
$ pyidevice instruments fps

{'currentTime': '2021-05-11 14:14:40.259059', 'fps': 52}
{'currentTime': '2021-05-11 14:14:40.259059', 'fps': 56}
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
$ instruments stackshot --out stackshot.log

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


QQ 交流群：37042417


使用文档: [查看文档](./doc/使用文档.md)
使用demo: [查看demo](./test/test.py)


# py-ios-device
[![PyPI](https://img.shields.io/pypi/v/py-ios-device)](https://pypi.org/project/py-ios-device/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/py-ios-device)](https://pypistats.org/search/py-ios-device)

A python based Apple instruments protocol，you can get CPU, Memory and other metrics from real iOS devices



link: https://testerhome.com/topics/27159

[中文文档](README_CN.md)

Java link: https://github.com/YueChen-C/java-ios-device)

## pip :
    pip install py-ios-device
    
python version: 3.7 +
### Instruments：
- [x] Get system Memory and CPU data
- [x] Get processes Memory and CPU data
- [x] Get FPS data
- [x] Get network data
- [x] Set the device network status. eg: 2G, 3G ,100% Loss
- [x] Set the device behaves as though under a high thermal state
- [x] Monitoring app start、exit、background
- [x] Launch and Kill app
- [x] Run xctest. eg: WebDriverAgent
- [x] Dump core profile stack snapshot 
- [x] Analyze the core profile data stream
- [x] Get Metal GPU Counters


### Other 
- [x] Profiles & Device Management. eg: Install and uninstall Fiddler certificate
- [x] Get syslog
- [x] Get crash log
- [x] Get the captured packet traffic and forward it to wireshark
- [x] App install and uninstall 
- [x] Get device battery 
- [x] Set simulate-location options


## Usage：

## pip :
    > pip install py-ios-device
    > pyidevice --help
    > pyidevice instruments --help


#### Get device list

```bash
$ pyidevice devices
```

#### Get device info

```bash
$ pyidevice --udid=xxxxxx deviceinfo
```

#### Get System performance data

```bash
$ pyidevice instruments monitor 
Memory  >> {'App Memory': '699.69 MiB', 'Cached Files': '1.48 GiB', 'Compressed': '155.17 MiB', 'Memory Used': '1.42 GiB', 'Wired Memory': '427.91 MiB', 'Swap Used': '46.25 MiB'}
Network >> {'Data Received': '4.07 GiB', 'Data Received/sec': '4.07 GiB', 'Data Sent': '2.54 GiB', 'Data Sent/sec': '2.54 GiB', 'Packets in': 2885929, 'Packets in/sec': 6031576, 'Packets Out': 2885929, 'Packets Out/sec': 2885929}
Disk    >> {'Data Read': '117.91 GiB', 'Data Read/sec': 0, 'Data Written': '64.28 GiB', 'Data Written/sec': 0, 'Reads in': 9734132, 'Reads in/sec': 9734132, 'Writes Out': 6810640, 'Writes Out/sec': 6810640}

$ pyidevice instruments monitor --filter = memory
Memory  >> {'App Memory': '699.69 MiB', 'Cached Files': '1.48 GiB', 'Compressed': '155.17 MiB', 'Memory Used': '1.42 GiB', 'Wired Memory': '427.91 MiB', 'Swap Used': '46.25 MiB'}

```



#### Get Processes performance data

```bash
$ pyidevice instruments sysmontap --help
$ pyidevice instruments sysmontap  -b com.tencent.xin --proc_filter memVirtualSize,cpuUsage --processes --sort cpuUsage # 只显示 memVirtualSize,cpuUsage 参数的进程列表，且根据 cpuUsage 字段排序 

[('WeChat', {'cpuUsage': 0.03663705586691998, 'memVirtualSize': 2179284992, 'name': 'WeChat', 'pid': 99269})]
[('WeChat', {'cpuUsage': 0.036558268613227536, 'memVirtualSize': 2179284992, 'name': 'WeChat', 'pid': 99269})]


```
#### Get FPS data

```bash
$ pyidevice instruments fps

{'currentTime': '2021-05-11 14:14:40.259059', 'fps': 52}
{'currentTime': '2021-05-11 14:14:40.259059', 'fps': 56}
```

#### Get network data
```bash
$ pyidevice instruments networking
# Get all network data
"connection-update{\"RxPackets\": 2, \"RxBytes\": 148, \"TxPackets\": 2, \"TxBytes\": 263, \"RxDups\": 0, \"RxOOO\": 0, \"TxRetx\": 0, \"MinRTT\": 0.05046875, \"AvgRTT\": 0.05046875, \"ConnectionSerial\": 5}"
"connection-update{\"RxPackets\": 4, \"RxBytes\": 150, \"TxPackets\": 3, \"TxBytes\": 1431, \"RxDups\": 0, \"RxOOO\": 0, \"TxRetx\": 0, \"MinRTT\": 0.0539375, \"AvgRTT\": 0.0541875, \"ConnectionSerial\": 4}"

$ pyidevice instruments network_process -p com.tencent.xin 
# Get application network data
{403: {'net.packets.delta': 119, 'time': 1620720061.0643349, 'net.tx.bytes': 366715, 'net.bytes.delta': 63721, 'net.rx.packets.delta': 47, 'net.tx.packets': 633, 'net.rx.bytes': 34532, 'net.bytes': 401247, 'net.tx.bytes.delta': 56978, 'net.rx.bytes.delta': 6743, 'net.rx.packets': 169, 'pid': 403, 'net.tx.packets.delta': 72, 'net.packets': 802}}
{403: {'net.packets.delta': 13, 'time': 1620720076.2191892, 'net.tx.bytes': 1303204, 'net.bytes.delta': 5060, 'net.rx.packets.delta': 5, 'net.tx.packets': 2083, 'net.rx.bytes': 46736, 'net.bytes': 1349940, 'net.tx.bytes.delta': 4682, 'net.rx.bytes.delta': 378, 'net.rx.packets': 379, 'pid': 403, 'net.tx.packets.delta': 8, 'net.packets': 2462}}

```

#### Set device status. iOS version > 12

```bash
$ pyidevice instruments condition get
# Get device configuration information

$ pyidevice instruments condition set -c SlowNetworkCondition -p SlowNetwork2GUrban
# Set the device network status. eg: 2G, 3G ,100% Loss

$ pyidevice instruments condition set -c ThermalCondition -p ThermalCritical
# Set the device behaves as though under a high thermal state
```


#### Listen to app notifications
```bash
$ pyidevice instruments notifications
[{'execName': 'MobileNotes', 'state_description': 'Foreground Running', 'elevated_state_description': 'Foreground Running', 'displayID': 'com.apple.mobilenotes', 'mach_absolute_time': 27205542653928, 'appName': 'Notes', 'elevated_state': 8, 'timestamp': 1620714619.1264, 'state': 8, 'pid': 99367}]
[{'execName': 'MobileNotes', 'state_description': 'Background Running', 'elevated_state_description': 'Background Running', 'displayID': 'com.apple.mobilenotes', 'mach_absolute_time': 27205678872050, 'appName': 'Notes', 'elevated_state': 4, 'timestamp': 1620714624.802145, 'state': 4, 'pid': 99367}]
[{'execName': 'MobileNotes', 'state_description': 'Background Task Suspended', 'elevated_state_description': 'Background Task Suspended', 'displayID': 'com.apple.mobilenotes', 'mach_absolute_time': 27205683486410, 'appName': 'Notes', 'elevated_state': 2, 'timestamp': 1620714624.99441, 'state': 2, 'pid': 99367}]
```

#### Dump core profile stack snapshot 
```bash
$ instruments stackshot --out stackshot.log

```

#### Analyze the core profile data stream 
```bash
$ instruments instruments core_profile --pid=1107
SealTalk(1107)             PERF_THD_CSwitch (0x25010014)                               DBG_PERF          PERF_DATA                     DBG_FUNC_NONE  
SealTalk(1107)             MACH_DISPATCH (0x1400080)                                   DBG_MACH          DBG_MACH_SCHED                DBG_FUNC_NONE  
SealTalk(1107)             DecrSet (0x1090004)                                         DBG_MACH          DBG_MACH_EXCP_DECI            DBG_FUNC_NONE  

```


#### Get Metal GPU Counters
```bash
$ instruments gpu_counters
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

### Other
#### Profiles & Device Management 

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
## install charles certificate

$ pyidevice profiles remove --name fe7371d9ce36c541ac8dee5f51f3b490b2aa98dcd95699ee44717fd5233fe7a0a
## uninstall charles certificate
```

#### get syslog
```bash
$ pyidevice syslog
# --path
# --filter
```


#### get crash syslog

```bash
$ pyidevice crash list
['.', '..', 'com.apple.appstored', 'JetsamEvent-2021-05-12-112126.ips']

$ pyidevice crash export --name JetsamEvent-2021-05-12-112126.ips

$ pyidevice crash delete --name JetsamEvent-2021-05-12-112126.ips

$ pyidevice crash shell

```


#### apps

```bash
$ pyidevice apps list

$ pyidevice apps install --ipa_path

$ pyidevice apps uninstall --bundle_id 

$ pyidevice apps launch --bundle_id

$ pyidevice apps kill --bundle_id

$ pyidevice apps shell 

```

#### packet traffic
```bash
$ pyidevice pcapd ./test/test.pacp

$ pyidevice pcapd - | "/Applications/Wireshark.app/Contents/MacOS/Wireshark" -k -i -
# mac forword Wireshark

$ pyidevice pcapd - | "D:\Program Files\Wireshark\Wireshark.exe" -k -i -
# win forword Wireshark

```

#### device battery
```bash
$ pyidevice battery
# [Battery] time=1622777708, current=-71, voltage=4330, power=-307.43, temperature=3279

```

#### enable developer mode
```bash
$ pyidevice enable_developer_mode
```


QQ ：37042417


api : [document](./doc/使用文档.md)
demo: [document](./test/test.py)


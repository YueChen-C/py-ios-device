# py-ios-device

A python based Apple instruments protocol，you can get CPU, Memory and other metrics from real iOS devices

win，mac 跨平台方案，通过 Instruments 私有协议获取 iOS 相关性能指标数据。

相关文章链接:https://testerhome.com/topics/27159

## pip 仓库:
    pip install py-ios-device
    
python 版本: 3.6+
### instruments 相关功能列表：
- [x] 获取 内存、cpu 数据
- [x] 获取 FPS 数据
- [x] 获取 网络数据
- [x] 设置模拟网络状态，例如 2g 、3g、 lost 等
- [x] 设置模拟设备高压过热状态
- [x] 事件监听，监听app 启动，退出，后台运行等
- [x] 启动杀死 APP
- [x] 运行 xcuitest 启动 wda


### 其他功能列表
- [ ] 获取系统日志流
- [ ] 获取崩溃日志
- [ ] 获取抓包数据转发至 wiershark
- [ ] 应用管理:安装、卸载、启动、查询、运行状态等
- [ ] 截图
- [ ] 打开 wifi 连接模式

## 命令行使用文档：

## pip 仓库:
    > pip install py-ios-device
    > pyidevice --help
    > pyidevice instruments --help


#### 获取性能数据

```bash
$ pyidevice instruments sysmontap --help
$ pyidevice instruments sysmontap --proc_filter memVirtualSize,cpuUsage --processes --sort cpuUsage 
# 只显示 memVirtualSize,cpuUsage 参数的进程列表，且根据 cpuUsage 字段排序 

```
#### 获取 FPS 数据

```bash
$ pyidevice instruments fps
```

#### 获取 网络数据
```bash
$ pyidevice instruments networking
```

#### 设置设备状态 iOS 版本 > 12
可以模拟网络状态，例如 2g 、3g、 lost 等<br>
可以模拟设备高压过热状态
```bash
$ pyidevice instruments condition get
# 获取设备状态配置信息

$ pyidevice instruments condition set
# 模拟网络状态，例如 2g 、3g、 lost 等

$ pyidevice instruments condition set
# 模拟设备高压过热状态
```


QQ 交流群：37042417

使用文档: [查看文档](./doc/使用文档.md)

使用demo: [查看demo](./test/test.py)

## LICENSE
[MIT](LICENSE)
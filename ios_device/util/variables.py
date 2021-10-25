import enum


class DgbFuncQual(enum.Enum):
    DBG_FUNC_NONE = 0
    DBG_FUNC_START = 1
    DBG_FUNC_END = 2


class LOG(str, enum.Enum):
    Instrument = 'Instrument'
    LockDown = "LockDown"
    xctest = "xctest"
    USBMux = 'USBMux'
    Mobile = 'Mobile'
    DTXMsg = 'DTXMsg'


class LockdownService(str, enum.Enum):
    MobileLockdown = 'com.apple.mobile.lockdown'
    MobileWirelessLockdown = "com.apple.mobile.wireless_lockdown"

    MobileScreenshotr = "com.apple.mobile.screenshotr"  # 截图服务
    MobileHouseArrest = "com.apple.mobile.house_arrest"  # 访问文件内的沙箱
    AppleAFC = "com.apple.afc"  # 访问系统资源
    InstrumentsRemoteServer = "com.apple.instruments.remoteserver"
    InstrumentsRemoteServerSecure = "com.apple.instruments.remoteserver.DVTSecureSocketProxy"
    TestmanagerdLockdown = "com.apple.testmanagerd.lockdown"
    TestmanagerdLockdownSecure = "com.apple.testmanagerd.lockdown.secure"


class InstrumentsService(str, enum.Enum):
    DeviceInfo = 'com.apple.instruments.server.services.deviceinfo'  # 获取设备信息
    # _selector
    # - machTimeInfo
    # - runningProcesses
    # - nameForGID:
    # - execnameForPid:
    # - isRunningPid:
    # - machKernelName
    # - symbolicatorSignatureForPid: trackingSelector:
    # - unregisterSignatureTrackingForPid:
    # - enableExpiredPidTracking:
    # - symbolicatorSignaturesForExpiredPids
    # - directoryListingForPath:
    # - iconDescriptionFileForAppPath:
    # - hardwareInformation
    # - traceCodesFile
    # - kpepDatabase
    # - sysmonProcessAttributes
    # - sysmonSystemAttributes
    # - sysmonCoalitionAttributes
    # - systemInformation
    # - networkInformation
    # - nameForUID:
    ProcessControl = "com.apple.instruments.server.services.processcontrol"  # 控制应用进程
    # _selector
    # - stopObservingPid:
    # - launchSuspendedProcessWithDevicePath:bundleIdentifier:environment:arguments:options:
    # - sendSignal:toPid:
    # - startObservingPid:
    # - suspendPid:
    # - resumePid:
    # - killPid:
    # - sendProcessControlEvent:toPid:
    Sysmontap = "com.apple.instruments.server.services.sysmontap"  # 获取应用性能数据
    # _selector
    # - setConfig: {'ur,'bm','procAttrs','sysAttrs','cpuUsage','sampleInterval'}
    # - fetchDataNow
    # - pause
    # - stop
    # - start
    # - unpause
    Networking = 'com.apple.instruments.server.services.networking'  # 全局网络数据
    # _selector
    # - replayLastRecordedSession
    # - stopMonitoring
    # - setTargetPID:
    # - startMonitoring
    MobileNotifications = 'com.apple.instruments.server.services.mobilenotifications'  # 监控应用状态
    # _selector
    # - setApplicationStateNotificationsEnabled:
    # - setMemoryNotificationsEnabled:
    GraphicsOpengl = "com.apple.instruments.server.services.graphics.opengl"  # 获取 FPS
    # _selector
    # - startSamplingAtTimeInterval:processIdentifier:
    # - startSamplingAtTimeInterval:
    # - availableStatistics
    # - driverNames
    # - valueForSwitch:
    # - setValue: forSwitchName:
    # - setSamplingRate:
    # - stopSampling
    # - cleanup
    ApplicationListing = "com.apple.instruments.server.services.device.applictionListing"  # 获取应用数据
    # _selector
    # - installedApplicationsMatching: registerUpdateToken:
    # - unregisterUpdateToken:
    XcodeNetworkStatistics = 'com.apple.xcode.debug-gauge-data-providers.NetworkStatistics'  # 获取单进程网络数据
    CoreProfileSessionTap = "com.apple.instruments.server.services.coreprofilesessiontap"  # 获取内核数据
    # _selector
    # - fetchDataNow
    # - pause
    # - stop
    # - start
    # - unpause
    # - setConfig:
    Screenshot = 'com.apple.instruments.server.services.screenshot'  # 获取画面
    # _selector
    # - takeScreenshot
    ConditionInducer = "com.apple.instruments.server.services.ConditionInducer"  # 控制手机，比如网络，手机状态
    # - availableConditionInducers
    # - disableActiveCondition
    # - disableConditionWithIdentifier:
    # - enableConditionWithIdentifier: profileIdentifier:
    XcodeEnergy = 'com.apple.xcode.debug-gauge-data-providers.Energy'
    GPU = 'com.apple.instruments.server.services.gpu'

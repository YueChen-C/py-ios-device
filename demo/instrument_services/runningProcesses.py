"""
查看所有正在运行的进程信息
"""
from instrument.RPC import get_usb_rpc


def runningProcesses(rpc):
    rpc.start()
    running = rpc.call("com.apple.instruments.server.instrument_services.deviceinfo", "runningProcesses").parsed
    print("runningProcesses:")
    headers = '\t'.join(sorted(running[0].keys()))
    print(headers)
    for item in running:
        sorted_item = sorted(item.items())
        print('\t'.join(map(str, [v for _, v in sorted_item])))
    rpc.stop()


if __name__ == '__main__':
    rpc = get_usb_rpc()
    runningProcesses(rpc)
    rpc.deinit()
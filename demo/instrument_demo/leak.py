"""
采集内存泄漏: 泄漏地址 + 内存图 (Instruments Leaks)。

目标 App 必须可调试 (开发签名 / get-task-allow), 并用 MallocStackLogging=1 启动,
否则报告里只有地址、没有调用栈。

用法:
    python demo/instrument_demo/leak.py [bundle_id] [udid]
"""

import os
import sys
import time

sys.path.append(os.getcwd())

from ios_device.cli.base import InstrumentsBase


def main(bundle_id: str, udid: str = None):
    with InstrumentsBase(udid=udid) as rpc:
        pid = rpc.launch_app(
            bundle_id=bundle_id,
            app_env={"MallocStackLogging": "1"},
            options={"StartSuspendedKey": 0, "KillExisting": True},
        )
        print(f"pid: {pid}, waiting for leaks ...")
        time.sleep(5)

        graph = rpc.memgraph(pid)
        print(f"leaked_count: {graph.leaked_count}")
        for address in graph.leaked_addresses:
            print(f"  {address:#x}")

        if graph.has_graph:
            path = graph.save(f"leaks_{pid}.memgraph")
            print(f"memgraph: {path}")
            print(f"inspect with: leaks {path}")


if __name__ == "__main__":
    main(
        sys.argv[1] if len(sys.argv) > 1 else "com.example.LeakDemo",
        sys.argv[2] if len(sys.argv) > 2 else None,
    )

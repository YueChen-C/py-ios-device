import logging
import os
import sys
from pathlib import Path
from typing import Optional

import coloredlogs

gettrace = getattr(sys, 'gettrace', None)
HOME_PATH = '.cache/pyidevice'


def hexdump(d):
    for i in range(0, len(d), 16):
        data = d[i:i + 16]
        print("%08X | %s | %s" % (i, hex(data).ljust(47), ascii(data)))


def read_file(filename):
    f = open(filename, "rb")
    data = f.read()
    f.close()
    return data


coloredlogs.DEFAULT_FIELD_STYLES = {'asctime': {'color': 'green'}, 'hostname': {'color': 'magenta'},
                                    'levelname': {'color': 'green', 'bold': True},
                                    'name': {'color': 'blue'}, 'programname': {'color': 'cyan'},
                                    'threadName': {'color': 'yellow'}}


class Log:
    __instances = {}

    def __init__(self, level=None):
        self.level = level

    @classmethod
    def getLogger(cls, name=os.path.abspath(__name__)) -> logging.Logger:
        if name not in cls.__instances:
            logger = logging.getLogger(name)
            fmt = '%(asctime)s [%(levelname)s] [%(name)s] %(filename)s[line:%(lineno)d] %(message)s'
            formater = logging.Formatter(fmt)
            ch = logging.StreamHandler()
            ch.setLevel(Log.__getLogLevel())
            ch.setFormatter(formater)
            logger.addHandler(ch)
            coloredlogs.install(fmt=fmt, level=Log.__getLogLevel(), logger=logger)
            logger.setLevel(Log.__getLogLevel())
            cls.__instances[name] = logger
        return cls.__instances[name]

    @staticmethod  # 设置日志等级
    def __getLogLevel():
        if os.getenv("DEBUG") in ("1", "on", "true"):
            return logging.DEBUG
        if os.getenv("ERROR") in ("1", "on", "true"):
            return logging.ERROR
        if gettrace():
            return logging.DEBUG
        else:
            return logging.INFO


PROGRAM_NAME = "py_ios_device"


def get_home_path(filename: str) -> Path:
    path = Path('~').expanduser().joinpath(HOME_PATH)
    if not path.exists():
        path.mkdir(parents=True)
    return path.joinpath(filename)


def read_home_file(filename: str) -> Optional[bytes]:
    path = get_home_path(filename)
    if not path.exists():
        return None
    with path.open('rb') as f:
        return f.read()


def write_home_file(filename: str, data: bytes) -> str:
    path = get_home_path(filename)
    with path.open('wb') as f:
        f.write(data)
    return path.as_posix()


def get_lockdown_dir():
    if sys.platform == 'win32':
        return Path(os.environ['ALLUSERSPROFILE'] + '/Apple/Lockdown/')
    else:
        return Path('/var/db/lockdown/')

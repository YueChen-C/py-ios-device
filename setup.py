"""
@Date    : 2020-12-18
@Author  : liyachao
"""
import setuptools
from setuptools import setup

# 第三方依赖
requires = [
    "cffi==1.14.4",
    "construct==2.10.56",
    "cryptography==3.3.2",
    "pyasn1==0.4.8",
    "pycparser==2.20",
    "pyOpenSSL==20.0.0",
    "six==1.15.0",
    "numpy==1.15.1"
]
setup(name='py_ios_device',
      version="1.0.2",
      description='Get ios data and operate ios devices',
      author='chenpeijie & liyachao',
      author_email='me@aaronsw.com',
      maintainer='chenpeijie & liyachao',
      maintainer_email='',
      url='https://github.com/YueChen-C/py-ios-device',
      packages=['ios_device.util', 'ios_device.servers', 'ios_device'],
      long_description="",
      license="Public domain",
      platforms=["any"],
      install_requires=requires,  # 第三方库依赖
      )

"""
@Date    : 2020-12-18
@Author  : liyachao
"""
from setuptools import setup,find_packages

# 第三方依赖
requires = [
    "cffi==1.14.4",
    "construct==2.10.56",
    "cryptography==3.3.2",
    "pyasn1==0.4.8",
    "pycparser==2.20",
    "pyOpenSSL==20.0.0",
    "six==1.15.0",
    "requests>=2.25.1",
    'click>=7.1.2',
    'coloredlogs>=3.3.2',

]
setup(name='py_ios_device',
      version="2.1.8",
      description='Get ios data and operate ios devices',
      author='chenpeijie & liyachao',
      author_email='cpjsf@163.com',
      maintainer='chenpeijie & liyachao',
      maintainer_email='',
      url='https://github.com/YueChen-C/py-ios-device',
      packages=find_packages(),
      long_description=open('README.md').read(),
      long_description_content_type="text/markdown",
      platforms=["any"],
      install_requires=requires,  # 第三方库依赖
      entry_points={
          'console_scripts':{
              'pyidevice=ios_device.main:cli'
          }
      },
      )

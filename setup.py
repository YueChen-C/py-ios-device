"""
@Date    : 2020-12-18
@Author  : liyachao
"""
from setuptools import setup, find_packages
from ios_device import __version__

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()]


setup(name='py_ios_device',
      version=__version__,
      description='Get ios data and operate ios devices',
      author='chenpeijie',
      author_email='cpjsf@163.com',
      maintainer='chenpeijie',
      maintainer_email='',
      url='https://github.com/YueChen-C/py-ios-device',
      packages=find_packages(),
      long_description=open('README.md').read(),
      long_description_content_type="text/markdown",
      install_requires=REQUIREMENTS,
      python_requires=">=3.7",
      include_package_data=True,
      classifiers=[
          "Programming Language :: Python :: 3",
          "Operating System :: OS Independent",
      ],
      entry_points={
          'console_scripts':{
              'pyidevice=ios_device.main:cli'
          }
      },
)

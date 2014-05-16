from setuptools import setup
import sys
import os
import shutil
import subprocess

setup(
    name='XsTools',
    version='0.1.15',
    description='Classes for interfacing with XESS FPGA boards via USB.',
    long_description=open('README.txt').read(),
    author='XESS Corp.',
    author_email='info@xess.com',
    url='http://pypi.python.org/pypi/XsTools/',
    classifiers=['License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',],
    packages=['xstools'],
    package_data={'xstools': ['xula*/*/*/*.bit', 'xula*/Firmware/*.hex', '*.rules', 'icons/*.png']},
    scripts=['bin/xstools_defs.py', 'bin/xstest.py', 'bin/xsload.py', 'bin/xsusbprg.py', 'bin/gxstools.py'],
    install_requires=['pypubsub >= 3.1.2', 'pyusb >= 1.0.0a3', 'bitstring >= 3.1.1', 'intelhex >= 1.4'],
    )

if 'install' in sys.argv or 'install_data' in sys.argv:
    if os.name != 'nt':
        try:
            shutil.copy('xstools/81-xstools-usb.rules', '/etc/udev/rules.d')
            subprocess.call(['udevadm', 'control', '--reload_rules'])
            subprocess.call(['udevadm', 'trigger'])
        except IOError:
            pass
        
if 'uninstall' in sys.argv:
    if os.name != 'nt':
        try:
            os.remove('/etc/udev/rules.d/81-xstools-usb.rules')
        except OSError:
            pass

import setuptools

import xstools

import sys
import os
import shutil
import subprocess

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'pypubsub >= 3.1.2',
    'pyusb >= 1.0.0a3, <1.0.0b1', 
    'bitstring >= 3.1.1', 
    'intelhex >= 1.4',
]

test_requirements = [  # TODO: put package test requirements here
]


setup(
    name='XsTools',
    version=xstools.__version__,
    description='Tools and classes for interfacing with XESS FPGA boards via USB.',
    long_description=readme + '\n\n' + history,
    author=xstools.__author__,
    author_email=xstools.__email__,
    url='https://github.com/xesscorp/XSTOOLs',
#    packages=['xstools'],
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts':[
            'usb2serial = xstools.usb2serial:usb2serial',
            'xsflags = xstools.xsflags:xsflags',
            'xsload = xstools.xsload:xsload',
            'xsmfgtest = xstools.xsmfgtest2:xsmfgtest',
            'xstest = xstools.xstest:xstest',
            'xsusbprg = xstools.xsusbprg:xsusbprg',
        ],
        'gui_scripts':[
            'gxstools = xstools.gxstools:gxstools',
        ],
    },
    package_dir={'xstools': 'xstools'},
# Don't set include_package_data to True! Then it only includes data files under version control.
#    include_package_data=True,
    package_data={'xstools': ['xula*/*.bit', 'xula*/*.hex', '*.rules', 'icons/*.png']},
    install_requires=requirements,
    license="GPLv2+",
    zip_safe=False,
    keywords='xstools',
    classifiers=['Development Status :: 2 - Pre-Alpha',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
                 'Natural Language :: English',
                 "Programming Language :: Python :: 2",
                 'Programming Language :: Python :: 2.6',
                 'Programming Language :: Python :: 2.7', ],
    test_suite='tests',
    tests_require=test_requirements,
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

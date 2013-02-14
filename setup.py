from setuptools import setup

setup(
    name='XsTools',
    version='0.1.2',
    author='XESS Corp.',
    author_email='info@xess.com',
    packages=['xstools'],
    package_data={'xstools': ['xula*/*/*/*.bit']},
    scripts=['bin/xstest.py', 'bin/xsload.py', 'bin/xsusbprg.py'],
    url='http://pypi.python.org/pypi/XsTools/',
    license='LICENSE.TXT',
    description='Classes for interfacing with XESS FPGA boards via USB.',
    long_description=open('README.txt').read(),
    install_requires=['pypubsub', 'pyusb', 'bitarray', 'intelhex'],
    )


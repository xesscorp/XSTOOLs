XSTOOLs
===============================

.. image:: https://img.shields.io/pypi/v/xstools.svg
        :target: https://pypi.python.org/pypi/XsTools

XSTOOLs is a collection of Python classes for interfacing to
XESS FPGA boards through a USB connection.

There are also several examples of command-line
utilities that use these classes to perform operations on
XESS boards.

* Free software: GPL V3 license
* Documentation: https://xstools.readthedocs.org.

Features
--------------------------------

* Python package for accessing XuLA FPGA boards through a USB link.
* Command-line tools for configuring the FPGA, uploading/downloading the
  serial flash and SDRAM, and running diagnostics on the board.
* GUI tool that performs the same functions as the command-line tools.

Installation
--------------------------------

XSTOOLs utilities use [PyUSB](https://walac.github.io/pyusb/). PyUSB relies on a
native system library for USB access. Instructions below will cover tested
libraries.

Install for a single user with the following commands:

* Windows:
```
pip install --user -r requirements.txt
python setup.py install --home=$HOME
```

* MacOS: [HomeBrew](http://brew.sh/) is a great choice for installing system
libraries.
```
<.travis/brew.txt xargs brew install
pip install --user -r requirements.txt
python setup.py install --home=$HOME
```

* Linux: You must install [wxPython Phoenix](https://github.com/wxWidgets/Phoenix/blob/master/README.rst)
from source.
```
﻿sudo apt-get install freeglut3-dev libgtk2.0-dev libgstreamer-plugins-base0.10-dev libwebkitgtk-dev libnotify-dev ﻿libsdl1.2-dev
wget http://wxpython.org/Phoenix/snapshot-builds/wxPython_Phoenix-3.0.3.dev2076+9cbca77.tar.gz
tar -zxvf wxPython_Phoenix-3.0.3.dev2076+9cbca77.tar.gz
python build.py dox etg --nodoc sip build

﻿sudo apt-get install libusb-1.0.0-dev
pip install --user -r requirements.txt
python setup.py install --home=$HOME
```

Running Graphical User Interface
--------------------------------

* MacOS:
```
PYTHONPATH=$PYTHONPATH:. pythonw xstools/gxstools.py
```

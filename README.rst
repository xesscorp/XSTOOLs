===============================
XSTOOLs
===============================

.. image:: https://img.shields.io/travis/xesscorp/xstools.svg
        :target: https://travis-ci.org/xesscorp/XsTools

.. image:: https://img.shields.io/pypi/v/xstools.svg
        :target: https://pypi.python.org/pypi/XsTools


XSTOOLs is a collection of Python classes for interfacing to
XESS FPGA boards through a USB connection.

Look in the ``bin`` to see several examples of command-line
utilities that use these classes to perform operations on
XESS boards.

* Free software: GPL V3 license
* Documentation: https://xstools.readthedocs.org.

Features
--------

* Python package for accessing XuLA FPGA boards through a USB link.
* Command-line tools for configuring the FPGA, uploading/downloading the
  serial flash and SDRAM, and running diagnostics on the board.
* GUI tool that performs the same functions as the command-line tools.

.. include:: docs/installation.rst

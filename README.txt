==========================
XSTOOLs
==========================

XSTOOLs is a collection of Python classes for interfacing to
XESS FPGA boards through a USB connection.

Look in the ``bin`` to see several examples of command-line
utilities that use these classes to perform operations on
XESS boards.

Install steps for Ubuntu/Debian
==========================
sudo apt-get install python-setuptools
git clone git://github.com/xesscorp/XSTOOLs.git
cd XSTOOLs
python setup.py build
sudo python setup.py install

cd
xsload.py --help


Contributors
==========================

* Dave Vandenbout wrote the original C++ version of XSTOOLs
  and the majority of the Python version.

* John Bowman wrote a Python version of xsload. Hector Peraza 
  modified the python code to eliminate some problems and make 
  FPGA configuration via JTAG conform to accepted practice.
  Dave took ideas and bits from Hector's code and integrated them 
  into this package.
  
* Al Neissner wrote a Python version of xsusbprg and bits of
  his code are used in this package.
  
* Alireza Moini added the methods for reading voltages
  from the XuLA board analog I/O pins. Dave modified these
  to output floating-point values.

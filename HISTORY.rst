.. :changelog:

History
-------

v0.1.30 (2015-09-02) 
---------------------

* Removed include in README.rst that caused an error generating the documentation.

v0.1.29 (2015-08-10) 
---------------------

* Specifying the board model on the CLI utilities is now case-insensitive.

v0.1.28 (2015-08-09) 
---------------------

* Now supports pyusb versions 1.0.0a and 1.0.0b.
* The utilities only connect to the USB port when they are actively executing
  some function for the attached XESS board. This allows other utilities to
  access the board.
* Added drag-and-drop capability for selecting bitstream and hex files.
* A history of bitstream and hex files is maintained.
* Exceptions caused by pyusb on program termination are now caught and filtered out.

v0.1.27 (2015-07-31) 
---------------------

* Removed scripts in bin directory and placed them in the xstools directory.
* Added entrypoints to generate executables for the XSTOOLs scripts. 
                       
v0.1.26 (2015-06-06) 
---------------------

* Changed distribution to use readthedocs for documentation.
                       
v0.1.25 (2015-06-05) 
---------------------

* Fixed problem where flash and SDRAM couldn't be accessed in gxstools
  because I appended 'bitstream' to the attribute names.
                       
v0.1.24 (2015-03-16) 
---------------------

* Modified usb2serial.py to prevent accidental triggering of serial BREAK.

v0.1.23 (2015-02-03) 
---------------------

* Modified usb2serial.py and xscomm.py to support new serial BREAK command.
* Added .cmd file to initiate each XSTOOLs script in a Windows command window.

v0.1.22 (2015-01-26) 
---------------------

* Modified usb2serial.py to support non-ZPUino use of the USB-to-serial server.

v0.1.21 (2015-01-07) 
---------------------

* Modified setup.py so pyusb < 1.0.0b1 is installed as a dependency since the
  newer 1.0.0bX libraries cause a problem with finding XESS boards on USB ports. 

V0.1.20 (2014-12-17) 
---------------------

* Modified setup.py to include microcontroller firmware hex files for the XESS
  boards. 

V0.1.19 (2014-12-12) 
---------------------

* Modified setup.py so pyusb <= 1.0.0b1 is installed as a dependency since the
  newer 1.0.0b2 library causes a problem with finding XESS boards on USB ports. 

v0.1.18 (2014-12-10) 
---------------------

* Fixed query for XESS USB devices which failed for some USB libraries.

v0.1.17 (2014-11-06) 
---------------------

* Fixed handling of XuLA/XuLA2 boards with old firmware or with the USB-to-JTAG
  path disabled.

v0.1.16 (2014-10-27) 
---------------------

* Added command-line and GUI methods for setting/getting flags in XuLA/XuLA2 boards.
* Enabled loading of .bit files into serial configuration flash via gxstools.
* Updated hex file to newest version of the PIC 18F14K50 firmware.
* Added USB-to-serial bridge server between XuLA board and virtual comm port on PC.
                       
v0.1.15 (2014-05-16) 
---------------------

* Added support for upload/download of signed integers to memio methods.

v0.1.14 (2014-05-05) 
---------------------

* Fixed FPGA bitstreams to remove errors during SDRAM upload/download.

v0.1.13 (2014-04-09) 
---------------------

* Add bidirectional communication channel between host and FPGA: xscomm.py.

v0.1.12 (2014-02-03) 
---------------------

* Added graphical front-end to XSTOOLs: gxstools.py.

v0.1.11 (2014-01-03) 
---------------------

* Fixed bit direction for checking status bits in xsi2c.py.

v0.1.10 (2013-11-20) 
---------------------

* Added support for XuLA2-LX9 board.

v0.1.9 (2013-05-15) 
---------------------

* Added ability to load Xilinx bitstream files directly into serial configuration flash.
* Fixed byte order of addresses sent to the W25X serial flash.
                    
v0.1.8 (2013-05-14)
--------------------

* Fixed FlashDev class so address bounds could not go outside the min/max addresses for the device.
                    
v0.1.7 (2013-05-11)
--------------------

* Added FlashDevice class for reading/writing flash memory devices.
* Made Pic18f14k50 class inherit from the FlashDevice class for flash read/write operations.
* Added routines for reading/writing serial configuration flash on the XuLA and XuLA2 boards.
* Extended xsload.py to enable serial flash uploading and downloading.
                    
v0.1.6 (2013-04-30)
--------------------

* Fixed xsusbprg.py so it works under linux.
* Fixed USB read/write timeouts so they are dependent upon the amount of data transferred.
* Replaced exit() with sys.exit() in scripts.
                    
v0.1.5 (2013-04-19)
--------------------

* Added XuLA firmware .hex files for use with xsusbprg.py.
* Fixed xsusbprg.py so it would upgrade XuLA board firmware by default.
* All user-accessible scripts now use xstools_defs.py to get a unified version #.
* Added .rules file for USB connections to XESS boards.
                    
v0.1.4 (2013-04-01)
--------------------

* Replaced bitarray module with pure-Python bitstring module.
                    
v0.1.3 (2013-02-15)
--------------------

* Fixed so multiple XsUsb objects can share a single USB link to access an XESS board.
                    
v0.1.2 (2013-02-14)
--------------------

* Changed CR-LF EOL in .py files to LF EOL so linux wouldn't barf.
                    
v0.1.1 (2013-01-23)
--------------------

* Use pypubsub instead of wxpython for publish/subscribe communications.
                    
v0.1.0 (2013-01-06)
--------------------

* Initial release.

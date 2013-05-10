#!/usr/bin/python
# -*- coding: utf-8 -*-
# **********************************************************************
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 2
#   of the License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
#   02111-1307, USA.
#
#   (c)2012 - X Engineering Software Systems Corp. (www.xess.com)
# **********************************************************************

"""
USB interface class for XESS FPGA boards.
"""

import time
import logging
import sys
import os
import math
import struct
import usb.core
import usb.util
from xserror import *

class XsUsb:

    """USB interface class for XESS FPGA board."""

    _VENDOR_ID = 0x04d8
    _PRODUCT_ID = 0xff8c
    _DEFAULT_ENDPOINT = 0x01
    _BIT_RATE = 1.0e6 # USB bit-rate of 1 Mbps.
    _MIN_TIME_OUT = 500 # Smallest timeout for USB read or write operation.

    #  Commands understood by XESS FPGA boards.
    READ_VERSION_CMD = 0x00  # Read the product version information.
    READ_FLASH_CMD = 0x01  # Read from the device flash.
    WRITE_FLASH_CMD = 0x02  # Write to the device flash.
    ERASE_FLASH_CMD = 0x03  # Erase the device flash.
    READ_EEDATA_CMD = 0x04  # Read from the device EEPROM.
    WRITE_EEDATA_CMD = 0x05  # Write to the device EEPROM.
    READ_CONFIG_CMD = 0x06  # Read from the device configuration memory.
    WRITE_CONFIG_CMD = 0x07  # Write to the device configuration memory.
    ID_BOARD_CMD = 0x31  # Flash the device LED to identify which device is being communicated with.
    UPDATE_LED_CMD = 0x32  # Change the state of the device LED.
    INFO_CMD = 0x40  # Get information about the USB interface.
    SENSE_INVERTERS_CMD = 0x41  # Sense inverters on TCK and TDO pins of the secondary JTAG port.
    TMS_TDI_CMD = 0x42  # Send a single TMS and TDI bit.
    TMS_TDI_TDO_CMD = 0x43  # Send a single TMS and TDI bit and receive TDO bit.
    TDI_TDO_CMD = 0x44  # Send multiple TDI bits and receive multiple TDO bits.
    TDO_CMD = 0x45  # Receive multiple TDO bits.
    TDI_CMD = 0x46  # Send multiple TDI bits.
    RUNTEST_CMD = 0x47  # Pulse TCK a given number of times.
    NULL_TDI_CMD = 0x48  # Send string of TDI bits.
    PROG_CMD = 0x49  # Change the level of the FPGA PROGRAM# pin.
    SINGLE_TEST_VECTOR_CMD = 0x4a  # Send a single, byte-wide test vector.
    GET_TEST_VECTOR_CMD = 0x4b  # Read the current test vector being output.
    SET_OSC_FREQ_CMD = 0x4c  # Set the frequency of the DS1075 oscillator.
    ENABLE_RETURN_CMD = 0x4d  # Enable return of info in response to a command.
    DISABLE_RETURN_CMD = 0x4e  # Disable return of info in response to a command.
    JTAG_CMD = 0x4f  # Send multiple TMS & TDI bits while receiving multiple TDO bits.
    FLASH_ONOFF_CMD = 0x50  # Enable/disable the FPGA configuration flash.
    AIO0_ADC_CMD = 0x60   # Do an ADC conversion on AIO0 (AN6 pin on pic)
    AIO1_ADC_CMD = 0x61   # Do an ADC conversion on AIO1 (AN11 pin on pic)

    RESET_CMD = 0xff  # Cause a power-on reset.

    # Flag fields for the JTAG_CMD.
    GET_TDO_MASK = 0x01  # Read bits from JTAG TDO pin.
    PUT_TMS_MASK = 0x02  # Write bits to JTAG TMS pin.
    TMS_VAL_MASK = 0x04  # Place a static value on the TMS pin.
    PUT_TDI_MASK = 0x08  # Write bits to the JTAG TDI pin.
    TDI_VAL_MASK = 0x10  # Place a static value on the TDI pin.

    BOOT_SELECT_FLAG_ADDR = 0xff
    BOOT_INTO_REFLASH_MODE = 0x3a
    BOOT_INTO_USER_MODE = 0xc5

    JTAG_DISABLE_FLAG_ADDR = 0xfd
    DISABLE_JTAG = 0x69

    FLASH_ENABLE_FLAG_ADDR = 0xfe
    ENABLE_FLASH = 0xac
    
    # This array will store the currently-active XESS USB devices.
    _xsusb_devs = []
    # This array stores discarded USB devices so their __del__ method doesn't kick in.
    _usb_discard_pile = []

    # Linux ioctl numbers made easy!
    # WDIOC_GETSUPPORT = _IOR(ord('W'), 0, "=II32s")

    # constant for linux portability
    _IOC_NRBITS = 8
    _IOC_TYPEBITS = 8

    # architecture specific
    _IOC_SIZEBITS = 14
    _IOC_DIRBITS = 2

    _IOC_NRMASK = (1 << _IOC_NRBITS) - 1
    _IOC_TYPEMASK = (1 << _IOC_TYPEBITS) - 1
    _IOC_SIZEMASK = (1 << _IOC_SIZEBITS) - 1
    _IOC_DIRMASK = (1 << _IOC_DIRBITS) - 1

    _IOC_NRSHIFT = 0
    _IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
    _IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
    _IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

    _IOC_NONE = 0
    _IOC_WRITE = 1
    _IOC_READ = 2

    def _IOC(dir, type, nr, size):
        if isinstance(size, str) or isinstance(size, unicode):
            size = struct.calcsize(size)
        return dir  << _IOC_DIRSHIFT  | \
               type << _IOC_TYPESHIFT | \
               nr   << _IOC_NRSHIFT   | \
               size << _IOC_SIZESHIFT

    def _IO(type, nr): return _IOC(_IOC_NONE, type, nr, 0)
    def _IOR(type, nr, size): return _IOC(_IOC_READ, type, nr, size)
    def _IOW(type, nr, size): return _IOC(_IOC_WRITE, type, nr, size)
    def _IOWR(type, nr, size): return _IOC(_IOC_READ | _IOC_WRITE, type, nr, size)

    @classmethod
    def get_xsusb_ports(cls):
        """Return the device descriptors for all XESS boards attached to USB ports."""

        # Get the currently-active XESS USB devices.
        # The find() routine throws exceptions under linux when XESS boards are
        # connected/reconnected, so catch the exceptions.
        while(True):
            try:
                devs = usb.core.find(idVendor=cls._VENDOR_ID,
                       idProduct=cls._PRODUCT_ID, find_all=True)
                break # Exit the loop once find() completes without an exception.
            except usb.core.USBError:
                pass # Keep trying until no exceptions occur.
            
        # Compare them to the previous set of active XESS USB devices.
        for i in range(len(devs)):
            for d in cls._xsusb_devs:
                if devs[i].bus == d.bus and devs[i].address == d.address:
                    # Re-use a previously-assigned XESS USB device instead of the new device
                    # so that multiple devices can share the USB link to a single XESS board.
                    devs[i] = d
                    
        # Update the array of currently-active XESS USB devices.
        cls._xsusb_devs = devs
        return cls._xsusb_devs

    @classmethod
    def get_num_xsusb(cls):
        """Return the number of XESS boards attached to USB ports."""

        return len(cls.get_xsusb_ports())
        
    def get_xsusb_id(self):
        devs = XsUsb.get_xsusb_ports()
        indexed_devs = zip(range(0,len(devs)), devs)
        for index, dev in indexed_devs:
            if (self._dev.bus, self._dev.address) == (dev.bus, dev.address):
                return index
        return None

    def __init__(self, xsusb_id=0, endpoint=1):
        """Initiate a USB connection to an XESS board."""

        devs = XsUsb.get_xsusb_ports()
        if devs == []:
            raise XsMinorError('XESS USB device could not be found.')
        self._xsusb_id = xsusb_id
        self._dev = devs[xsusb_id]
        self._endpoint = endpoint
        self.terminate = False
        
    def _calc_time_out(self,num_bytes):
        """Calculate USB transaction interval (in milliseconds) for a given bit-rate."""
        return max(int(math.ceil(num_bytes * 8 / self._BIT_RATE * 1000)), self._MIN_TIME_OUT)

    def write(self, bytes):
        """Write a byte array to an XESS board."""
        
        if self.terminate:
            self.terminate = False
            raise XsTerminate()

        logging.debug('OUT => (%d) %s', len(bytes), str([bin(x | 0x100)[3:] for x in bytes]))
        time_out = self._calc_time_out(len(bytes))
        if self._dev.write(usb.util.ENDPOINT_OUT | self._endpoint,
                           bytes, 0, time_out) \
            != len(bytes):
            raise XsMajorError('Failed to write required number of bytes over the USB link')

    def read(self, num_bytes=0):
        """Return a byte array read from an XESS board."""

        if self.terminate:
            self.terminate = False
            raise XsTerminate()

        time_out = self._calc_time_out(num_bytes)
        bytes = self._dev.read(usb.util.ENDPOINT_IN | self._endpoint,
                               num_bytes, 0, time_out)
        if len(bytes) != num_bytes:
            raise XsMajorError('Failed to read required number of bytes over the USB link'
                               )
        logging.debug('IN <= (%d %d) %s', len(bytes), num_bytes,
                      str([bin(x | 0x100)[3:] for x in bytes]))
        return bytes

    def set_prog(self, level):
        """Change the level on the PROG# pin of the FPGA."""

        cmd = bytearray([self.PROG_CMD, level])
        self.write(cmd)
        
    def disconnect(self):
        """Disconnect the XESS Board from the USB link."""
        if self._dev != None:
            usb.util.dispose_resources(self._dev)
            # linux has a hard time when deleting USB ports that no longer exist,
            # so keep the USB devices on a discard pile so they won't get cleaned.
            self._usb_discard_pile.append(self._dev)
            self._dev = None
        
    def _is_connected(self):
        """Determine if the XsUsb object's USB connection is still present."""
        
        # Store previous XSUSB devices.
        prev_devs = self._xsusb_devs[:]

        # Get all active XsUsb devices.
        devs = XsUsb.get_xsusb_ports()

        # Look for one with the same address and bus as this one.
        for i in range(len(devs)):
            if devs[i].bus == self._dev.bus and devs[i].address == self._dev.address:
                self._dev = devs[i]
                return True # This device is connected.

        # Look for a different port that wasn't there before.
        for i in range(len(devs)):
            new_port = True
            for j in range(len(prev_devs)):
                if devs[i].bus == prev_devs[j].bus and devs[i].address == prev_devs[j].address:
                    new_port = False
                    break
            if new_port:
                # linux throws exceptions when deleting USB ports that no longer exist,
                # so keep the USB devices on a discard pile so they won't get cleaned.
                self._usb_discard_pile.append(self._dev)
                # Assume this newly-discovered port is the one connected to this XESS board.
                self._dev = devs[i]
                return True
        
        # Keep the USB device around to remember the bus & address where it was connected.
        return False # This device is not connected.
        
    def reset(self):
        """Reset the XESS board."""
        
        # Reset the XESS board.
        cmd = bytearray([self.RESET_CMD])
        self.write(cmd)
        
        # Reset the USB connection to the board.
        if os.name == 'nt':
            # On Windows, this re-enumerates the USB devices.
            self._dev.reset()
        else:
            # Use ioctl to do a USB reset. *** THIS DID NOT WORK! ***
            # import fcntl
            # usb_device_filename = os.path.join('/dev/bus/usb', '%03d' % self._dev.bus, '%03d' % self._dev.address)
            # fd = open(usb_device_filename, 'a+b')
            # fcntl.ioctl(fd, _IO(ord('U'), 20))
            # linux doesn't re-enumerate the USB port when reset(), so a manual disconnect/reconnect handles that.
            print 'Please disconnect your XESS board ...',
            sys.stdout.flush()
        
        # Wait for the USB connection to disappear.
        while self._is_connected():
            pass
            
        if os.name != 'nt':
            print 'thanks!'
            print 'Please reconnect your XESS board ...',
            sys.stdout.flush()
            
        # Wait for the USB connection to re-establish itself.
        while not self._is_connected():
            pass
            
        # Let's be polite to our linux friends.
        if os.name != 'nt':
            print 'thanks!'
            sys.stdout.flush()
            
    def get_info(self):
        """Return the info string stored in the XESS board."""

        cmd = bytearray([self.INFO_CMD])
        self.write(cmd)
        return self.read(32)

    def adc_aio0(self):
        """Return the voltage on AIO0."""

        cmd = bytearray([self.AIO0_ADC_CMD])
        self.write(cmd)
        v = self.read(3)
        return (v[1]*256 + v[2]) / 1023.0 * 2.048

    def adc_aio1(self):
        """Return the voltage on AIO1."""

        cmd = bytearray([self.AIO1_ADC_CMD])
        self.write(cmd)
        v = self.read(3)
        return (v[1]*256 + v[2]) / 1023.0 * 2.048


if __name__ == '__main__':
    # Get the number of XESS USB devices out there.
    while(True):
        sys.stdout.write('Plug it in...\n')
        while XsUsb.get_num_xsusb() == 0:
            pass
        xsusb = XsUsb()
        sys.stdout.write('Pull it out...\n')
        while XsUsb.get_num_xsusb() != 0:
            pass
            
    # Create a link for talking over USB to an XESS USB device.
    xsusb = XsUsb()
    xsusb.reset()
    xsusb.reset()
    xsusb.reset()
    # Just write something to the device and see if it responds (i.e., its LED blinks).
    #xsusb.write([0x01, 0x02, 0x03, 0x04])

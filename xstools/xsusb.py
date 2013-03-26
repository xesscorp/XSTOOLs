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
import usb.core
import usb.util
from xserror import *


class XsUsb:

    """USB interface class for XESS FPGA board."""

    _VENDOR_ID = 0x04d8
    _PRODUCT_ID = 0xff8c
    _DEFAULT_ENDPOINT = 0x01
    _USB_XFER_TIMEOUT = 1000  # USB read/write transfer timeout in milliseconds.

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

    @classmethod
    def get_xsusb_ports(cls):
        """Return the device descriptors for all XESS boards attached to USB ports."""

        # Get the currently-active XESS USB devices.
        devs = usb.core.find(idVendor=cls._VENDOR_ID,
                   idProduct=cls._PRODUCT_ID, find_all=True)
                   
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
        
    def get_hash(self):
        return 256 * self._bus + self._address
        
    def get_xsusb_id(self):
        hash = self.get_hash()
        devs = XsUsb.get_xsusb_ports()
        indexed_devs = zip(range(0,len(devs)), devs)
        for index, dev in indexed_devs:
            if hash == 256 * dev.bus + dev.address:
                return index
        return None

    def __init__(self, xsusb_id=0, endpoint=1):
        """Initiate a USB connection to an XESS board."""

        devs = XsUsb.get_xsusb_ports()
        if devs == []:
            raise XsMinorError('XESS USB device could not be found.')
        self._xsusb_id = xsusb_id
        self._dev = devs[xsusb_id]
        self._address = devs[xsusb_id].address
        self._bus = devs[xsusb_id].bus
        self._endpoint = endpoint
        self.terminate = False

    def write(self, bytes):
        """Write a byte array to an XESS board."""
        
        if self.terminate:
            self.terminate = False
            raise XsTerminate()

        logging.debug('OUT => (%d) %s', len(bytes), str([bin(x | 0x100)[3:] for x in bytes]))
        if self._dev.write(usb.util.ENDPOINT_OUT | self._endpoint,
                           bytes, 0, self._USB_XFER_TIMEOUT) \
            != len(bytes):
            raise XsMajorError('Failed to write required number of bytes over the USB link')

    def read(self, num_bytes=0x00):
        """Return a byte array read from an XESS board."""

        if self.terminate:
            self.terminate = False
            raise XsTerminate()

        bytes = self._dev.read(usb.util.ENDPOINT_IN | self._endpoint,
                               num_bytes, 0, self._USB_XFER_TIMEOUT)
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
        """Disconnect the XESS board from the USB link."""
        if self._dev != None:
            usb.util.dispose_resources(self._dev)
        self._dev = None

    def reset(self):
        """Reset the XESS board."""

        cmd = bytearray([self.RESET_CMD])
        self.write(cmd)
        self.disconnect()
        time.sleep(2)
        self.__init__(self._xsusb_id, self._endpoint)

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

    def erase_flash(self, address):
        """Erase a block of flash in the microcontroller."""

        num_blocks = 1
        cmd = bytearray([self.ERASE_FLASH_CMD, num_blocks])
        cmd.extend(bytearray([address & 0xff, address >> 8 & 0xff,
                   address >> 16 & 0xff]))
        self.write(cmd)
        response = self.read(num_bytes=1)
        if response[0] != self.ERASE_FLASH_CMD:
            raise XsMajorError("Incorrect command echo in 'erase_flash'."
                               )

    def write_flash(self, address, bytes):
        """Write data to a block of flash in the microcontroller."""

        cmd = bytearray([self.WRITE_FLASH_CMD, len(bytes)])
        cmd.extend(bytearray([address & 0xff, address >> 8 & 0xff,
                   address >> 16 & 0xff]))
        cmd.extend(bytearray(bytes))
        self.write(cmd)
        response = self.read(num_bytes=1)
        if response[0] != self.WRITE_FLASH_CMD:
            raise XsMajorError("Incorrect command echo in 'write_flash'."
                               )

    def read_flash(self, address, num_bytes=0):
        """Read data from the flash in the microcontroller."""

        cmd = bytearray([self.READ_FLASH_CMD, num_bytes])
        cmd.extend(bytearray([address & 0xff, address >> 8 & 0xff,
                   address >> 16 & 0xff]))
        self.write(cmd)
        response = self.read(num_bytes=num_bytes + len(cmd))
        if response[0] != self.READ_FLASH_CMD:
            raise XsMajorError("Incorrect command echo in 'read_flash'."
                               )
        return response[5:]

    def read_eedata(self, address):
        """Return a byte read from the microcontroller EEDATA."""

        cmd = bytearray([self.READ_EEDATA_CMD, 1])
        cmd.extend(bytearray([address & 0xff, address >> 8 & 0xff,
                   address >> 16 & 0xff]))
        self.write(cmd)
        response = self.read(num_bytes=6)
        if response[0] != self.READ_EEDATA_CMD:
            raise XsMajorError("Incorrect command echo in 'read_eedata'."
                               )
        return response[5]

    def write_eedata(self, address, byte):
        """Write a byte to the microcontroller EEDATA."""

        cmd = bytearray([self.WRITE_EEDATA_CMD, 1])
        cmd.extend(bytearray([address & 0xff, address >> 8 & 0xff,
                   address >> 16 & 0xff]))
        cmd.extend(bytearray([byte]))
        self.write(cmd)
        response = self.read(num_bytes=1)
        if response[0] != self.WRITE_EEDATA_CMD:
            raise XsMajorError("Incorrect command echo in 'write_eedata'."
                               )

    def enter_reflash_mode(self):
        """Set EEDATA mode flag and reset microcontroller into flash programming mode."""

        self.write_eedata(self.BOOT_SELECT_FLAG_ADDR,
                          self.BOOT_INTO_REFLASH_MODE)
        self.reset()

    def enter_user_mode(self):
        """Set EEDATA mode flag and reset microcontroller into user mode."""

        self.write_eedata(self.BOOT_SELECT_FLAG_ADDR,
                          self.BOOT_INTO_USER_MODE)
        self.reset()

    def enable_jtag_cable(self):
        """Set EEDATA flag to enable JTAG cable interface."""

        self.write_eedata(self.JTAG_DISABLE_FLAG_ADDR, 0)

    def disable_jtag_cable(self):
        """Set EEDATA flag to disable JTAG cable interface."""

        self.write_eedata(self.JTAG_DISABLE_FLAG_ADDR,
                          self.DISABLE_JTAG)


if __name__ == '__main__':
    # Get the number of XESS USB devices out there.
    print '#XSUSB = %d' % XsUsb.get_num_xsusb()
    # Create a link for talking over USB to an XESS USB device.
    xsusb = XsUsb()
    # Just write something to the device and see if it responds (i.e., its LED blinks).
    xsusb.write([0x01, 0x02, 0x03, 0x04])

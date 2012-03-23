#!/usr/bin/python
# -*- coding: utf-8 -*-

# /***********************************************************************************
# *   This program is free software; you can redistribute it and/or
# *   modify it under the terms of the GNU General Public License
# *   as published by the Free Software Foundation; either version 2
# *   of the License, or (at your option) any later version.
# *
# *   This program is distributed in the hope that it will be useful,
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# *   GNU General Public License for more details.
# *
# *   You should have received a copy of the GNU General Public License
# *   along with this program; if not, write to the Free Software
# *   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# *   02111-1307, USA.
# *
# *   (c)2012 - X Engineering Software Systems Corp. (www.xess.com)
# ***********************************************************************************/

"""
USB interface to XESS FPGA boards.
"""

import logging
import usb.core
import usb.util


class XsUsb:

    """USB interface object for XESS FPGA board."""

    _VENDOR_ID = 0x04d8
    _PRODUCT_ID = 0xff8c
    _DEFAULT_ENDPOINT = 0x01
    _USB_XFER_TIMEOUT = 1000  # USB read/write transfer timeout in milliseconds.

    #  Commands understood by XESS FPGA boards.
    READ_VERSION_CMD       = 0x00  # Read the product version information.
    READ_FLASH_CMD         = 0x01  # Read from the device flash.
    WRITE_FLASH_CMD        = 0x02  # Write to the device flash.
    ERASE_FLASH_CMD        = 0x03  # Erase the device flash.
    READ_EEDATA_CMD        = 0x04  # Read from the device EEPROM.
    WRITE_EEDATA_CMD       = 0x05  # Write to the device EEPROM.
    READ_CONFIG_CMD        = 0x06  # Read from the device configuration memory.
    WRITE_CONFIG_CMD       = 0x07  # Write to the device configuration memory.
    ID_BOARD_CMD           = 0x31  # Flash the device LED to identify which device is being communicated with.
    UPDATE_LED_CMD         = 0x32  # Change the state of the device LED.
    INFO_CMD               = 0x40  # Get information about the USB interface.
    SENSE_INVERTERS_CMD    = 0x41  # Sense inverters on TCK and TDO pins of the secondary JTAG port.
    TMS_TDI_CMD            = 0x42  # Send a single TMS and TDI bit.
    TMS_TDI_TDO_CMD        = 0x43  # Send a single TMS and TDI bit and receive TDO bit.
    TDI_TDO_CMD            = 0x44  # Send multiple TDI bits and receive multiple TDO bits.
    TDO_CMD                = 0x45  # Receive multiple TDO bits.
    TDI_CMD                = 0x46  # Send multiple TDI bits.
    RUNTEST_CMD            = 0x47  # Pulse TCK a given number of times.
    NULL_TDI_CMD           = 0x48  # Send string of TDI bits.
    PROG_CMD               = 0x49  # Change the level of the FPGA PROGRAM# pin.
    SINGLE_TEST_VECTOR_CMD = 0x4a  # Send a single, byte-wide test vector.
    GET_TEST_VECTOR_CMD    = 0x4b  # Read the current test vector being output.
    SET_OSC_FREQ_CMD       = 0x4c  # Set the frequency of the DS1075 oscillator.
    ENABLE_RETURN_CMD      = 0x4d  # Enable return of info in response to a command.
    DISABLE_RETURN_CMD     = 0x4e  # Disable return of info in response to a command.
    JTAG_CMD               = 0x4f  # Send multiple TMS & TDI bits while receiving multiple TDO bits.
    FLASH_ONOFF_CMD        = 0x50  # Enable/disable the FPGA configuration flash.
    RESET_CMD              = 0xff  # Cause a power-on reset.

    # Flag fields for the JTAG_CMD.
    GET_TDO_MASK = 0x01  # Read bits from JTAG TDO pin.
    PUT_TMS_MASK = 0x02  # Write bits to JTAG TMS pin.
    TMS_VAL_MASK = 0x04  # Place a static value on the TMS pin.
    PUT_TDI_MASK = 0x08  # Write bits to the JTAG TDI pin.
    TDI_VAL_MASK = 0x10  # Place a static value on the TDI pin.

    @classmethod
    def get_num_xsusb(cls):
        """Return the number of XESS boards attached to USB ports."""

        return len(usb.core.find(idVendor=cls._VENDOR_ID,
                   idProduct=cls._PRODUCT_ID, find_all=True))

    def __init__(self, xsusb_id=0x00, endpoint=0x01):
        """Initiate a USB connection to an XESS board."""

        devs = usb.core.find(idVendor=self._VENDOR_ID,
                             idProduct=self._PRODUCT_ID, find_all=True)
        if devs == []:
            raise ValueError('XESS USB device not found')
        self._dev = devs[xsusb_id]
        self._endpoint = endpoint

    def write(self, data):
        """Write a byte array to an XESS board."""

        logging.debug('OUT => (%d) %s', len(data),
            str([bin(x | 0x100)[0x03:] for x in data]))
        self._dev.write(usb.util.ENDPOINT_OUT | self._endpoint, data,
                        0x00, self._USB_XFER_TIMEOUT)

    def read(self, num_bytes=0x00):
        """Return a byte array read from an XESS board."""

        data = self._dev.read(usb.util.ENDPOINT_IN | self._endpoint,
                              num_bytes, 0x00, self._USB_XFER_TIMEOUT)
        logging.debug('IN <= (%d %d) %s', len(data), num_bytes, 
            str([bin(x | 0x100)[0x03:] for x in data]))
        return data
        
    def set_prog(self, bit_val):
        self.write(bytearray([self.PROG_CMD,bit_val]))


if __name__ == '__main__':
    # Get the number of XESS USB devices out there.
    print '#XSUSB = %d' % XsUsb.get_num_xsusb()
    # Create a link for talking over USB to an XESS USB device.
    xsusb = XsUsb()
    # Just write something to the device and see if it responds (i.e., its LED blinks).
    xsusb.write([0x01, 0x02, 0x03, 0x04])

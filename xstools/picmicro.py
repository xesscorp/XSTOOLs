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
PIC microcontroller classes.
"""

import sys
from xsusb import *
from flashdev import *

    
class Pic18f14k50(FlashDevice):
    """PIC18F14K50 microcontroller."""
    
    device_name = 'PIC 18F14K50'

    _START_ADDR = 0x0800
    _END_ADDR = 0x4000
    _ERASE_BLK_SZ = 64
    _WRITE_BLK_SZ = 16
    _READ_BLK_SZ = 16

    def __init__(self, xsusb=None):
        self._xsusb = xsusb

    def _addr_bytes(self, addr):
        return bytearray([addr & 0xff, addr >> 8 & 0xff, addr >> 16 & 0xff])
        
    def erase_blk(self, addr):
        """Erase a block of flash in the microcontroller."""

        num_blocks = 1
        cmd = bytearray([self._xsusb.ERASE_FLASH_CMD, num_blocks])
        cmd.extend(self._addr_bytes(addr))
        self._xsusb.write(cmd)
        response = self._xsusb.read(num_bytes=1)
        if response[0] != cmd[0]:
            raise XsMajorError("Incorrect command echo in %s." % sys.sys._getframe().f_code.co_name)

    def write_blk(self, addr, data):
        """Write data to a block of flash in the microcontroller."""

        cmd = bytearray([self._xsusb.WRITE_FLASH_CMD, len(data)])
        cmd.extend(self._addr_bytes(addr))
        cmd.extend(bytearray(data))
        self._xsusb.write(cmd)
        response = self._xsusb.read(num_bytes=1)
        if response[0] != cmd[0]:
            raise XsMajorError("Incorrect command echo in %s." % sys.sys._getframe().f_code.co_name)

    def read_blk(self, addr, num_bytes=0):
        """Read data from the flash in the microcontroller."""

        cmd = bytearray([self._xsusb.READ_FLASH_CMD, num_bytes])
        cmd.extend(self._addr_bytes(addr))
        self._xsusb.write(cmd)
        response = self._xsusb.read(num_bytes=num_bytes + len(cmd))
        if response[0] != cmd[0]:
            raise XsMajorError("Incorrect command echo in %s." % sys.sys._getframe().f_code.co_name)
        return response[5:]

    def read_eedata(self, addr):
        """Return a byte read from the microcontroller EEDATA."""

        cmd = bytearray([self._xsusb.READ_EEDATA_CMD, 1])
        cmd.extend(self._addr_bytes(addr))
        self._xsusb.write(cmd)
        response = self._xsusb.read(num_bytes=6)
        if response[0] != cmd[0]:
            raise XsMajorError("Incorrect command echo in %s." % sys.sys._getframe().f_code.co_name)
        return response[5]

    def write_eedata(self, addr, byte):
        """Write a byte to the microcontroller EEDATA."""

        cmd = bytearray([self._xsusb.WRITE_EEDATA_CMD, 1])
        cmd.extend(self._addr_bytes(addr))
        cmd.extend(bytearray([byte]))
        self._xsusb.write(cmd)
        response = self._xsusb.read(num_bytes=1)
        if response[0] != cmd[0]:
            raise XsMajorError("Incorrect command echo in %s." % sys.sys._getframe().f_code.co_name)

    def enter_reflash_mode(self):
        """Set EEDATA mode flag and reset microcontroller into flash programming mode."""

        self.write_eedata(self._xsusb.BOOT_SELECT_FLAG_ADDR, self._xsusb.BOOT_INTO_REFLASH_MODE)
        self._xsusb.reset()

    def enter_user_mode(self):
        """Set EEDATA mode flag and reset microcontroller into user mode."""

        self.write_eedata(self._xsusb.BOOT_SELECT_FLAG_ADDR,
                          self._xsusb.BOOT_INTO_USER_MODE)
        self._xsusb.reset()

    def get_jtag_cable_flag(self):
        """Get EEDATA flag that enables/disables the JTAG cable interface."""

        return self.read_eedata(self._xsusb.JTAG_DISABLE_FLAG_ADDR)

    def set_jtag_cable_flag(self, flag):
        """Set EEDATA flag that enables/disables the JTAG cable interface."""

        self.write_eedata(self._xsusb.JTAG_DISABLE_FLAG_ADDR, flag)

    def enable_jtag_cable(self):
        """Set EEDATA flag to enable the JTAG cable interface."""

        self.set_jtag_cable_flag(0)

    def disable_jtag_cable(self):
        """Set EEDATA flag to disable the JTAG cable interface."""

        self.set_jtag_cable_flag(self._xsusb.DISABLE_JTAG)

    def get_cfg_flash_flag(self):
        """Get EEDATA flag that enables/disables the serial configuration flash."""

        return self.read_eedata(self._xsusb.FLASH_ENABLE_FLAG_ADDR)

    def set_cfg_flash_flag(self, flag):
        """Set the EEDATA flag that enables/disables the serial configuration flash."""

        self.write_eedata(self._xsusb.FLASH_ENABLE_FLAG_ADDR, flag)

    def enable_cfg_flash(self):
        """Set EEDATA flag to enable the serial configuration flash."""

        self.set_cfg_flash_flag(self._xsusb.ENABLE_FLASH)

    def disable_cfg_flash(self):
        """Set EEDATA flag to disable the serial configuration flash."""

        self.set_cfg_flash_flag(0)

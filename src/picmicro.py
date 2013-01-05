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
PIC microcontroller objects - from generic to more-specific subclasses.
"""

import logging
from intelhex import IntelHex
from xserror import *
from xsusb import *


class PicMicro:

    """Generic PIC microcontroller object."""

    def __init__(self, xsusb=None):
        """Initialize the PIC uC."""

        self.xsusb = xsusb

    def erase_flash(self, bottom=None, top=None):
        """Erase the non-boot section of the uC flash."""

        bottom = (self.USER_START if bottom == None else bottom)
        top = (self.USER_END if top == None else top)
        bottom = bottom & (1 << 32) - self.ERASE_BLOCK_SIZE
        top = int((top + self.ERASE_BLOCK_SIZE - 1)
                  / self.ERASE_BLOCK_SIZE) * self.ERASE_BLOCK_SIZE
        if bottom > top:
            raise XsMinorError('Bottom address is greater than the top address.')
        for address in range(bottom, top, self.ERASE_BLOCK_SIZE):
            self.xsusb.erase_flash(address)

    def write_flash(
        self,
        hexfile,
        bottom=None,
        top=None,
        ):
        """Download the hexfile into the uC flash."""

        bottom = (self.USER_START if bottom == None else bottom)
        top = (self.USER_END if top == None else top)
        # If the argument is not already a hex data object, then it must be a file name, so read the hex data from it.
        if not isinstance(hexfile, IntelHex):
            try:
                hexfile_data = IntelHex(hexfile)
                hexfile = hexfile_data
            except:
                raise XsMajorError('Unable to open hex file %s for writing to uC flash.'
                                    % hexfile)
        bottom = bottom & (1 << 32) - self.WRITE_BLOCK_SIZE
        top = int((top + self.WRITE_BLOCK_SIZE - 1)
                  / self.WRITE_BLOCK_SIZE) * self.WRITE_BLOCK_SIZE
        if bottom > top:
            raise XsMinorError('Bottom address is greater than the top address.')
        for address in range(bottom, top, self.WRITE_BLOCK_SIZE):
            # The tobinarray() method fills unused array locations with 0xFF so the flash at those
            # addresses will stay unprogrammed.
            self.xsusb.write_flash(address,
                                   bytearray(hexfile.tobinarray(start=address,
                                   size=self.WRITE_BLOCK_SIZE)))

    def read_flash(self, bottom=None, top=None):
        """Return the hex data stored in the uC flash."""

        bottom = (self.USER_START if bottom == None else bottom)
        top = (self.USER_END if top == None else top)
        bottom = bottom & (1 << 32) - self.WRITE_BLOCK_SIZE
        top = int((top + self.WRITE_BLOCK_SIZE - 1)
                  / self.WRITE_BLOCK_SIZE) * self.WRITE_BLOCK_SIZE
        if bottom > top:
            raise XsMinorError('Bottom address is greater than the top address.')
        data = bytearray()
        for address in range(bottom, top, self.READ_BLOCK_SIZE):
            data.extend(self.xsusb.read_flash(address,
                        self.READ_BLOCK_SIZE))
        hex_data = IntelHex()
        hex_data[bottom:top] = [byte for byte in data]
        return hex_data

    def verify_flash(
        self,
        hexfile,
        bottom=None,
        top=None,
        ):
        """Verify the program in the uC flash matches the hex file."""

        bottom = (self.USER_START if bottom == None else bottom)
        top = (self.USER_END if top == None else top)
        # If the argument is not already a hex data object, then it must be a file name, so read the hex data from it.
        if not isinstance(hexfile, IntelHex):
            try:
                hexfile_data = IntelHex(hexfile)
                hexfile = hexfile_data
            except:
                raise XsMajorError('Unable to open hex file %s for verifying uC flash.'
                                    % hexfile)
        bottom = bottom & (1 << 32) - self.WRITE_BLOCK_SIZE
        top = int((top + self.WRITE_BLOCK_SIZE - 1)
                  / self.WRITE_BLOCK_SIZE) * self.WRITE_BLOCK_SIZE
        if bottom > top:
            raise XsMinorError('Bottom address is greater than the top address.')
        flash = self.read_flash(bottom, top)
        errors = [(a, flash[a], hexfile[a]) for a in
                  sorted(hexfile.todict().keys()) if flash[a]
                  != hexfile[a] and bottom <= a < top]
        if len(errors) > 0:
            raise XsMajorError('uC flash != hex file at %d locations starting at address 0x%04x (0x%02x != 0x%02x)'
                                % (len(errors), errors[0][0],
                               errors[0][1], errors[0][2]))

    def program_flash(
        self,
        hexfile,
        bottom=None,
        top=None,
        ):
        """Erase, write and verify the uC flash with the contents of the hex file."""

        bottom = (self.USER_START if bottom == None else bottom)
        top = (self.USER_END if top == None else top)
        self.erase_flash(bottom, top)
        self.write_flash(hexfile, bottom, top)
        self.verify_flash(hexfile, bottom, top)


class Pic18f14k50(PicMicro):

    """PIC18F14K50 microcontroller."""

    BOOT_START = 0x0000
    BOOT_END = 0x0800
    USER_START = 0x0800
    USER_END = 0x4000
    ERASE_BLOCK_SIZE = 0x40
    WRITE_BLOCK_SIZE = 0x10
    READ_BLOCK_SIZE = 0x10

    def __init__(self, xsusb=None):
        PicMicro.__init__(self, xsusb=xsusb)



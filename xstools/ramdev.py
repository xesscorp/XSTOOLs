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
#   (c)2014 - X Engineering Software Systems Corp. (www.xess.com)
# **********************************************************************

"""
Classes for devices containing RAM memory.
"""

import logging
import struct
from intelhex import IntelHex
from xserror import *
from xsmemio import *


class RamDevice:

    """Generic RAM memory object."""

    def __init__(self, xsusb_id=DEFAULT_XSUSB_ID, module_id=DEFAULT_MODULE_ID, xsjtag=None):
        """Initialize the RAM."""
        self._ram = XsMemIo(xsusb_id=xsusb_id, module_id=module_id, xsjtag=xsjtag)
        
    def _set_blk_bounds(self, bottom, top, blk_sz):
        bottom = self._START_ADDR if (bottom == None or bottom < self._START_ADDR) else bottom
        top = self._END_ADDR if (top == None or top >= self._END_ADDR) else top
        if bottom > top:
            raise XsMinorError('Bottom address is greater than the top address.')
        return (bottom, top)

    def erase(self, bottom=None, top=None):
        """Erase a section of the flash."""

        if bottom is None or top is None:
            raise XsMinorError('Must specify both top and bottom addresses to erase %s.', self._DEVICE_NAME)
            
        if bottom % self._WORD_SIZE != 0:
            raise XsMinorError('Bottom address must be a multiple of the %s word size (%x / %d != 0)' % (self._DEVICE_NAME, bottom, self._WORD_SIZE))
        num_bytes = (top-bottom+1)
        if num_bytes % self._WORD_SIZE != 0:
            raise XsMinorError('Number of bytes is not a multiple of the %s word size (%x / %d != 0)' % (self._DEVICE_NAME, num_bytes, self._WORD_SIZE))
            
        hex_data = IntelHex()
        for addr in range(bottom,top+1):
            hex_data[addr] = 0xff
        self.write(hex_data)

    def write(self, hexfile, bottom=None, top=None):
        """Download a hexfile into a section of the RAM."""

        # If the argument is not already a hex data object, then it must be a file name, so read the hex data from it.
        if not isinstance(hexfile, IntelHex):
            try:
                hexfile_data = IntelHex(hexfile)
                hexfile = hexfile_data
            except:
                # Error: neither an Intel hex or Xilinx bitstream file.
                raise XsMajorError('Unable to convert file %s for writing to %s.'
                                   % (hexfile, self._DEVICE_NAME))

        if bottom is None:
            bottom = hexfile.minaddr()
        if top is None:
            top = hexfile.maxaddr()
        # If min and/or max address is undefined, then hex data must be empty.
        if bottom is None or top is None:
            raise XsMinorError('No data to write.')
            
        # Convert the hex data byte-wise addresses into addresses for the word-size of the memory device.
        if bottom % self._WORD_SIZE != 0:
            raise XsMinorError('Bottom address must be a multiple of the %s word size (%x / %d != 0)' % (self._DEVICE_NAME, bottom, self._WORD_SIZE))
        num_bytes = (top-bottom+1)
        if num_bytes % self._WORD_SIZE != 0:
            raise XsMinorError('Number of bytes is not a multiple of the %s word size (%x / %d != 0)' % (self._DEVICE_NAME, num_bytes, self._WORD_SIZE))
        ram_bottom = bottom/self._WORD_SIZE
        num_words = num_bytes/self._WORD_SIZE
        
        # Convert the hex data into words for the RAM.
        hex_to_word_format = self._WORD_ENDIAN + str(num_words) + self._WORD_TYPE
        ram_words = struct.unpack(hex_to_word_format, hexfile.gets(bottom,num_bytes))
        
        # Write the words to the RAM.
        self._ram.write(ram_bottom, ram_words)

    def read(self, bottom=None, top=None):
        """Return the hex data stored in a section of the RAM."""

        if bottom is None or top is None:
            raise XsMinorError('Must specify both top and bottom addresses to read %s.', self._DEVICE_NAME)
            
        if bottom % self._WORD_SIZE != 0:
            raise XsMinorError('Bottom address must be a multiple of the %s word size (%x / %d != 0)' % (self._DEVICE_NAME, bottom, self._WORD_SIZE))
        num_bytes = (top-bottom+1)
        if num_bytes % self._WORD_SIZE != 0:
            raise XsMinorError('Number of bytes is not a multiple of the %s word size (%x / %d != 0)' % (self._DEVICE_NAME, num_bytes, self._WORD_SIZE))
        ram_bottom = bottom/self._WORD_SIZE
        num_words = num_bytes/self._WORD_SIZE
        
        ram_words = self._ram.read(ram_bottom, num_words, return_type=int())
        word_to_hex_format = self._WORD_ENDIAN + str(num_words) + self._WORD_TYPE
        hex_bytes = IntelHex()
        hex_bytes.puts(bottom, struct.pack(word_to_hex_format, *ram_words))
        return hex_bytes


class Sdram_8MB(RamDevice):

    """8MB SDRAM."""

    _START_ADDR = 0
    _END_ADDR = 2**23-1 # Max byte address, which is twice the word address.
    _WRITE_BLK_SZ = 256
    _READ_BLK_SZ = 256
    _WORD_SIZE = 2 # 16-bit word size.
    _WORD_TYPE = 'H' # 16-bit unsigned integers.
    _WORD_ENDIAN = '>' # Big-endian byte order.
    _DEVICE_NAME = '8MB SDRAM'


class Sdram_32MB(RamDevice):

    """32MB SDRAM."""

    _START_ADDR = 0
    _END_ADDR = 2**25-1 # Max byte address, which is twice the word address.
    _WRITE_BLK_SZ = 256
    _READ_BLK_SZ = 256
    _WORD_SIZE = 2 # 16-bit word size.
    _WORD_TYPE = 'H' # 16-bit unsigned integers.
    _WORD_ENDIAN = '>' # Big-endian byte order.
    _DEVICE_NAME = '32MB SDRAM'

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
Xilinx FPGA configuration bitstream object.
"""

import os
import struct
import logging
import string
from xserror import *
from xsbitarray import *


class XilinxBitstream:

    def __init__(self, filename=None):
        self.filename = filename
        self.design_name = None
        self.device_type = None
        self.compile_date = None
        self.compile_time = None
        self.bits = None
        if filename != None:
            self.from_file(filename=self.filename)

    def from_file(self, filename):
        """Load a bitstream from .bit file."""

        try:
            bitfile = ConstBitStream(filename=filename)
        except:
            raise XsMajorError("Unable to open file '%s'" % filename)
        self.filename = filename

        initial_offset = bitfile.read(16).uint * 8
        bitfile.pos += initial_offset
        if bitfile.read(16).uint != 1:
            raise XsMajorError("'%s' does not appear to be a bit file." % self.filename)

        # Field codes for the various fields of a Xilinx bitstream file.
        DESIGN_NAME_FC = 0x61
        DEVICE_TYPE_FC = 0x62
        COMPILE_DATE_FC = 0x63
        COMPILE_TIME_FC = 0x64
        BITSTREAM_FC = 0x65

        # Extract the fields from the bitstream file.
        while True:
            if bitfile.pos == bitfile.len:
                break  # EOF
            field_code = bitfile.read(8).uint
            if field_code == DESIGN_NAME_FC:
                field_length = bitfile.read(16).uint * 8
                # Get the string but clip-off the NUL character at the end.
                self.design_name = bitfile.read(field_length).tobytes()[:-1]
            elif field_code == DEVICE_TYPE_FC:
                field_length = bitfile.read(16).uint * 8
                # Get the string but clip-off the NUL character at the end.
                self.device_type = bitfile.read(field_length).tobytes()[:-1]
            elif field_code == COMPILE_DATE_FC:
                field_length = bitfile.read(16).uint * 8
                # Get the string but clip-off the NUL character at the end.
                self.compile_date = bitfile.read(field_length).tobytes()[:-1]
            elif field_code == COMPILE_TIME_FC:
                field_length = bitfile.read(16).uint * 8
                # Get the string but clip-off the NUL character at the end.
                self.compile_time = bitfile.read(field_length).tobytes()[:-1]
            elif field_code == BITSTREAM_FC:
                field_length = bitfile.read(32).uint * 8
                self.bits = XsBitArray(bitfile.read(field_length))
                self.bits.reverse()  # Reverse the config bits so the 1st bit to transmit is at the highest bit index.
            else:
                raise XsMajorError("Unknown field %d at position %d in bit file '%s'." % (field_code, bitfile.pos - 8, self.filename))

        logging.debug(
            'Bitstream file %s with design %s was compiled for %s at %s on %s into a bitstream of length %d',
            self.filename,
            self.design_name,
            self.device_type,
            self.compile_time,
            self.compile_date,
            self.bits.len,
            )
        logging.debug('Bitstream start = %s', self.bits[0:1024])

        return True
        
    def to_intel_hex(self):
        """Generate Intel hex object from bitstream."""
        
        PREAMBLE_LENGTH = 16
        preamble = XsBitArray(bytes=b'\xff' * PREAMBLE_LENGTH, length = 8 * PREAMBLE_LENGTH)
        bits = preamble + self.bits[:]
        bits.reverse()
        return bits.to_intel_hex()


if __name__ == '__main__':
    logging.root.setLevel(logging.DEBUG)
    xil_bitstream = XilinxBitstream('test.bit')

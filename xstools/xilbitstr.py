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
# Python 2 and 3: alternative 2: refactor the code to avoid considering
# byte-strings as strings.
from builtins import str

import logging

from bitstring import ConstBitStream

from xstools.xsbitarray import XsBitArray
from xstools.xserror import XsMajorError


class XilinxBitstream:
    # Field codes for the various fields of a Xilinx bitstream file.
    DESIGN_NAME_FC = 0x61
    DEVICE_TYPE_FC = 0x62
    COMPILE_DATE_FC = 0x63
    COMPILE_TIME_FC = 0x64
    BITSTREAM_FC = 0x65

    def __init__(self, filename=None):
        self.filename = filename
        self.design_name = None
        self.device_type = None
        self.compile_date = None
        self.compile_time = None
        self.bits = None
        if filename is not None:
            self.from_file(filename=self.filename)

    def from_file(self, filename):
        """Load a bitstream from .bit file."""
        try:
            self.filename = filename
            with open(filename, 'rb') as file_obj:
                bitfile = ConstBitStream(auto=file_obj)
                self._extract_fields(bitfile)
        except:
            raise XsMajorError("Unable to open file '%s'" % filename)

        return True

    def _extract_fields(self, bitfile):
        initial_offset = bitfile.read(16).uint * 8
        bitfile.pos += initial_offset
        if bitfile.read(16).uint != 1:
            fmt = "'%s' does not appear to be a bit file."
            raise XsMajorError(fmt % self.filename)

        # Extract the fields from the bitstream file.
        while True:
            if bitfile.pos == bitfile.len:
                break  # EOF
            field_code = bitfile.read(8).uint
            if field_code == self.DESIGN_NAME_FC:
                field_length = bitfile.read(16).uint * 8
                # Get the string but clip-off the NUL character at the end.
                self.design_name = bitfile.read(field_length).tobytes()[:-1]
                self.design_name = str(self.design_name, 'utf-8')
            elif field_code == self.DEVICE_TYPE_FC:
                field_length = bitfile.read(16).uint * 8
                # Get the string but clip-off the NUL character at the end.
                self.device_type = bitfile.read(field_length).tobytes()[:-1]
                self.device_type = str(self.device_type, 'utf-8')
            elif field_code == self.COMPILE_DATE_FC:
                field_length = bitfile.read(16).uint * 8
                # Get the string but clip-off the NUL character at the end.
                self.compile_date = bitfile.read(field_length).tobytes()[:-1]
                self.compile_date = str(self.compile_date, 'utf-8')
            elif field_code == self.COMPILE_TIME_FC:
                field_length = bitfile.read(16).uint * 8
                # Get the string but clip-off the NUL character at the end.
                self.compile_time = bitfile.read(field_length).tobytes()[:-1]
                self.compile_time = str(self.compile_time, 'utf-8')
            elif field_code == self.BITSTREAM_FC:
                field_length = bitfile.read(32).uint * 8
                self.bits = XsBitArray(bitfile.read(field_length))
                # Reverse the config bits so the 1st bit to transmit is at the
                # highest bit index.
                self.bits.reverse()
            else:
                msg_fmt = "Unknown field %d at position %d in bit file '%s'."
                msg = msg_fmt % (field_code, bitfile.pos - 8, self.filename)
                raise XsMajorError(msg)

        logging.debug(
            'Bitstream file %s with design %s was compiled for %s at %s on %s '
            'into a bitstream of length %d',
            self.filename,
            self.design_name,
            self.device_type,
            self.compile_time,
            self.compile_date,
            self.bits.len,
            )
        logging.debug('Bitstream start = %s', self.bits[0:1024])
        
    def to_intel_hex(self):
        """Generate Intel hex object from bitstream."""
        preamble_len = 16  # bytes
        preamble = XsBitArray(bytes=b'\xff'*preamble_len, length=8*preamble_len)
        bits = preamble + self.bits[:]
        bits.reverse()
        return bits.to_intel_hex()

    def __str__(self):
        keys = ['device_type', 'design_name', 'compile_date', 'compile_time']
        members = [(k, self.__dict__[k]) for k in keys]
        return '{}: {}'.format(self.__class__, members)


if __name__ == '__main__':
    logging.root.setLevel(logging.DEBUG)
    xil_bitstream = XilinxBitstream('test.bit')

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
Xilinx bitstream object.
"""

import os
import struct
import logging
import string
from xserror import *
from bitarray import bitarray


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
        """Load object from .bit file."""

        try:
        
            fptr = open(os.path.abspath(filename), 'rb')
        except:
            raise XsMajorError("Unable to open file '%s'" % filename)
        self.filename = filename

        def get_int(fptr):
            return struct.unpack('>H', fptr.read(2))[0]

        def get_word(fptr):
            return struct.unpack('>I', fptr.read(4))[0]

        fptr.seek(get_int(fptr), os.SEEK_CUR)
        if get_int(fptr) != 1:
            raise XsMajorError("'%s' does not appear to be a bit file."
                               % self.filename)

        # Field codes for the various fields of a Xilinx bitstream file.
        DESIGN_NAME_FC = 0x61
        DEVICE_TYPE_FC = 0x62
        COMPILE_DATE_FC = 0x63
        COMPILE_TIME_FC = 0x64
        BITSTREAM_FC = 0x65
        # Extract the fields from the bitstream file.
        while True:
            field_byte = fptr.read(1)
            if len(field_byte) == 0:
                break  # EOF
            field_code = ord(field_byte)
            if field_code == DESIGN_NAME_FC:
                field_length = get_int(fptr)
                self.design_name = fptr.read(field_length)
            elif field_code == DEVICE_TYPE_FC:
                field_length = get_int(fptr)
                self.device_type = filter(lambda x: x \
                        in string.printable, fptr.read(field_length))
            elif field_code == COMPILE_DATE_FC:
                field_length = get_int(fptr)
                self.compile_date = fptr.read(field_length)
            elif field_code == COMPILE_TIME_FC:
                field_length = get_int(fptr)
                self.compile_time = fptr.read(field_length)
            elif field_code == BITSTREAM_FC:
                field_length = get_word(fptr)
                self.bits = bitarray()
                self.bits.fromfile(fptr, field_length)
            else:
                raise XsMajorError("Unknown field in bit file '%s'."
                                   % self.filename)

        logging.debug(
            'Bitstream file %s with design %s was compiled for %s at %s on %s into a bitstream of length %d'
                ,
            self.filename,
            self.design_name,
            self.compile_time,
            self.device_type,
            self.compile_date,
            self.bits.length(),
            )
        logging.debug('Bitstream start = %s', self.bits[32 * 8:32
                      * 16].to01())

        return True


if __name__ == '__main__':
    logging.root.setLevel(logging.DEBUG)
    xil_bitstream = XilinxBitstream('test.bit')

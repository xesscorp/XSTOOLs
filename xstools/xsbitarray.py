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
XESS extensions to BitString-BitArray object.
"""

import logging
from xserror import *
from bitstring import Bits, BitArray, BitStream, ConstBitStream


class XsBitArray(BitArray):

    """Class for storing and manipulating bit vectors.
    
    All XsBitArray objects are stored with the LSB at index 0.
    """

    # @staticmethod
    # def from_int(num, num_of_bits=32):
        # """Convert an integer and return a bit array with the specified # of bits."""
        # bits = XsBitArray(uint=num, length=num_of_bits)
        # bits.reverse() # This gets us back to little-endian with least-significant bit in position 0.
        # return bits

    # def to_int(self):
        # """Return the integer representation of a bit array."""
        # bits = self[:] # Make a copy of the bit string.
        # bits.reverse() # Reverse it to bit order that BitArray expects. 
        # return bits.uint # Return the unsigned integer value of the bits.

    def to_usb_buffer(self):
        """Convert a bitstring into a byte array with the bits in each byte
           ordered correctly.
           XsBitArray order:      b0 b1 b2 b3 b4 b5 b6 b7 b8 b9 b10 b11 b12 b13 b14 b15 ...
           USB buffer bit order: |b7 b6 b5 b4 b3 b2 b1 b0|b15 b14 b13 b12 b11 b10 b9 b8|...
        """

        # Create a temporary bit array from this bit array, but guaranteed to have multiple-of-8 number of bits
        # with each 8-bit field flipped to account for the xmit reversal done in the XuLA firmware.
        
        bytes = self.tobytes() # Eight-bit bytes with 0 bits padded after the MS bit position.
        bytes = bytes[::-1] # Reverse the order of the bytes so last byte to send comes first.
        bits = XsBitArray(bytes=bytes) # Create a bit string from the bytes.
        bits.reverse() # Now reverse the order of the entire bit string.
        # At this point, the original bit string has been extended to a multiple of eight bits
        # and the order of each eight-bit field has been flipped.
        return bits.tobytes() # Return a byte array for sending over USB link.
        
    @staticmethod
    def from_usb_buffer(usb_buffer, num_bits=0):
        """Create a bitstring from a byte array received over USB
           so that the bit ordering of the bytes is correct.
           USB buffer bit order: |b7 b6 b5 b4 b3 b2 b1 b0|b15 b14 b13 b12 b11 b10 b9 b8|...
           XsBitArray order:      b0 b1 b2 b3 b4 b5 b6 b7 b8 b9 b10 b11 b12 b13 b14 b15 ...
        """
        
        bits = XsBitArray(bytes=usb_buffer)
        bits.reverse()
        bits.byteswap()
        if num_bits > 0:
            del bits[num_bits:]
        logging.debug('bitstring_from_usb_buffer => %s', bits)
        return bits

    # def __setattr__(self, name, val):
        # """Set the bit array from an integer, unsigned integer or string."""

        # if name == 'unsigned' or name == 'int' or name == 'integer':
            # self = XsBitArray.from_int(val, len(self))
        # elif name == 'string':
            # self = XsBitArray(val)
        # else:
            # super(XsBitArray, self).__setattr__(name, val)
        # return val

    # def __getattr__(self, name):
        # """Return the unsigned, integer or string representation of a bit array."""

        # if name == 'int' or name == 'integer':
            # val = self.to_int()
            # # Correct for sign bit.
            # if self[-1] == 1:
                # val -= 1 << self.length()
            # return val
        # elif name == 'unsigned':
            # # No need to correct for sign bit.
            # return self.to_int()
        # elif name == 'string':
            # return self.to01()
        # else:
            # return super(XsBitArray, self).__getattr__(name)


Bitvec = XsBitArray  # Associate old Bitvec class with new XsBitArray class.

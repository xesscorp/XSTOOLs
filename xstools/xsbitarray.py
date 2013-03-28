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
XESS extensions to the BitArray class of the bitstring module.
"""

import logging
from xserror import *
from bitstring import Bits, BitArray, BitStream, ConstBitStream


class XsBitArray(BitArray):

    """Class for storing and manipulating bit vectors.

    The main difference from the BitArray class is that XsBitArray
    objects store their least-significant bits in bit position 0.
    However, the BitArray constructor is used to make XsBitArray
    objects, so things like integers and binary strings are stored
    with their most-significant bits first. Therefore, the bits in
    these objects need to be reversed after they are created.
    """
    
    def __init__(self, *args, **kwargs):
        reverse = kwargs.pop('reverse',False)
        super(XsBitArray, self).__init__(*args, **kwargs)
        if reverse:
            self.reverse()

    def to_usb_buffer(self):
        """Convert a bitstring into a byte array with the bits in each byte
           ordered correctly for transmission over USB to an XESS board.
           XsBitArray order:      b0 b1 b2 b3 b4 b5 b6 b7 b8 b9 b10 b11 b12 b13 b14 b15 ...
           USB buffer bit order: |b7 b6 b5 b4 b3 b2 b1 b0|b15 b14 b13 b12 b11 b10 b9 b8|...
        """

        # Create a temporary bit array from this bit array, but guaranteed to have multiple-of-8 number of bits
        # with each 8-bit field flipped to account for the xmit reversal done in the XESS firmware.
        
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
        
        # Create a bit array from the USB bytes and then reverse the bit order of each byte.
        # Then truncate to the desired length starting from the most-significant bits.
        bits = XsBitArray(bytes=usb_buffer) # Create a bit string from the USB bytes.
        bits.reverse() # Reverse the entire string of bits so the first received bits are near the end.
        bits.byteswap() # Reverse the bytes so the first received bits are now at the start.
        # At this point, the original bytes in the USB buffer have each been reversed in place.
        # Now, truncate any unwanted bits from the last-received end of the bit string.
        if num_bits > 0:
            del bits[num_bits:]
        return bits

    def __getattr__(self, name):
        """Return the unsigned, integer or string representation of a bit array."""

        if name == 'int' or name == 'integer':
            bits = self[:]
            bits.reverse()
            return getattr(super(XsBitArray, bits), 'int')
        elif name == 'unsigned':
            bits = self[:]
            bits.reverse()
            return getattr(super(XsBitArray, bits), 'uint')
        elif name == 'string':
            bits = self[:]
            bits.reverse()
            return getattr(super(XsBitArray, bits), 'bin')[2:]
        else:
            return getattr(super(XsBitArray, bits), name)

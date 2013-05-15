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
from intelhex import IntelHex


class XsBitArray(BitArray):

    """Class for storing and manipulating bit vectors."""

    # The underlying bitstring class stores a bitstring such as 0b110010 with the
    # most-significant bit (1 in this case) in index position 0, and the least-significant
    # bit (0 in this case) in the highest index position (5 in this case).
    #
    # The bitstrings for the XESS boards typically contain strings of JTAG TDI and TMS
    # bits which are transmitted starting with the least-significant bit. This creates a
    # problem if a bitstring like 0b110010 is to be transmitted and followed by another
    # bitstring like 0b101011. Concatenating the bitstrings gives 0b110010101011, but the
    # actual transmission order should be 010011110101. It would be easier if the bitstrings
    # were concatenated in the reverse order as 101011110010 and then transmitted starting
    # from the highest bit index and proceeding down to index 0. To do this while expressing
    # the bit string concatenations in their more natural left-to-right order, the +, +=
    # and append operations were redefined to do their operations in the reverse order.
    # So a + b with XsBitArrays gives the same result as b + a with BitArrays.

    def append(self, bits):
        """Append the contents of a bitstring to this one, but in reverse order."""

        return super(XsBitArray, self).prepend(bits)

    def prepend(self, bits):
        """Prepend the contents of a bitstring to this one, but in reverse order."""

        return super(XsBitArray, self).append(bits)

    def __add__(self, bits):
        """Concatenate the contents of two bitstrings, but in the opposite order."""

        b = self._copy()
        b.append(bits)
        return b

    def __radd__(self, bits):
        """Concatenate the contents of two bitstrings, but in the opposite order."""

        b = self._copy()
        b.prepend(bits)
        return b

    def __iadd__(self, bits):
        """Append the contents of a bitstring to this one, but in reverse order."""

        self = self + bits
        return self

    def head(self, length=1):
        """Return the first set of transmitted or received bits from a bitstring."""

        return self[self.len - length:]

    def tail(self, length=1):
        """Return the last set of transmitted or received bits from a bitstring."""

        return self[:length]

    def pop_field(self, length):
        """Remove the first set of transmitted or received bits from a bitstring and return it."""

        field = self.head(length)  # Get the bits in the field.
        del self[self.len - length:]  # Remove the field from the bit string.
        return field

    def to_usb(self):
        """Convert a bitstring into a byte array with the bits in each byte
           ordered correctly for transmission over USB to an XESS board.
        """

        # The bit strings are stored with the first transmitted bit at the highest index like so:
        #       XsBitArray order: | b15 b14 b13 b12 b11 b10 b9 b8 | b7 b6 b5 b4 b3 b2 b1 b0 |
        # But the XESS board expects to get a USB packet with bytes where the least-significant bit
        # of the first byte is the first bit to transmit:
        #       USB buffer bit order: | b7 b6 b5 b4 b3 b2 b1 b0 | b15 b14 b13 b12 b11 b10 b9 b8 |
        # So this function pads the bit string so it consists of complete bytes, converts
        # the bitstring into bytes, and finally reverses the order of the bytes.
        bits = self + XsBitArray((8 - self.len % 8) % 8)  # Pad the bitstring to make complete bytes.
        return bits.tobytes()[::-1]  # Convert bit string to bytes and reverse their order.

    @staticmethod
    def from_usb(usb_bytes, length=0):
        """Create a bitstring from a byte array received over USB
           so that the bit ordering of the bytes is correct.
        """

        # The bytes sent by XESS boards contain the first received bit in the least-significant bit
        # of the first byte as follows:
        #       USB buffer bit order: | b7 b6 b5 b4 b3 b2 b1 b0 | b15 b14 b13 b12 b11 b10 b9 b8 |
        # This has to be converted into a bit string with the first received bit at the highest index like so:
        #       XsBitArray order: | b15 b14 b13 b12 b11 b10 b9 b8 | b7 b6 b5 b4 b3 b2 b1 b0 |
        # So this function reverses the byte order, creates a bit string, and then cuts it to length.
        bits = XsBitArray(bytes=usb_bytes[::-1])  # Create a bit string from the reversed USB bytes.
        return bits[-length:]
        
    def to_intel_hex(self):
        """Create an IntelHex object from a bitstring."""
        
        ih = IntelHex()
        ih.frombytes([ord(b) for b in self.tobytes()])
        return ih
        

    def __getattr__(self, name):
        """Return the unsigned, integer or string representation of a bit array."""

        if name == 'integer':
            name = 'int'
        elif name == 'unsigned':
            name = 'uint'
        elif name == 'string':
            name = 'bin'
        return getattr(super(XsBitArray, self), name)


if __name__ == '__main__':
    logging.root.setLevel(logging.DEBUG)
    a = XsBitArray('0b00010')
    b = XsBitArray('0b1111001')
    c = a + b
    print a, b, c
    print repr(c.to_usb())

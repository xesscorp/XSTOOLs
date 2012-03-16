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
XESS extensions to bitarray object.
"""

from bitarray import bitarray


class XsBitarray(bitarray):

    """Class for storing and manipulating bit vectors.
    
    All XsBitArray objects are stored with the LSB at index 0.
    """

    def __init__(self, initial=None):
        """Create a bit array and initialize it."""

        super(bitarray, self).__init__(initial, endian='little')

    @staticmethod
    def from_int(num, num_of_bits=32):
        """Convert an integer and return a bit array with the specified # of bits."""

        assert num < 1 << num_of_bits
        # Take the number and OR it with a mask to set the MSB+1 bit position.
        # This insures the binary representation has (num_of_bits+1) binary digits.
        # Then remove the leading '0b1' from the binary string.
        # Then reverse the binary string so the LSB is at position 0.
        # Then create a bit array using the binary string as the initializer.
        return XsBitarray(bin(num | 1 << num_of_bits)[3:][::-1])

    def to_int(self):
        """Return the integer representation of a bit array."""

        # Convert the bit array to a biinary string.
        # Then reverse the string so the LSB is in position 0.
        # Then convert the binary string (base 2) into an integer.
        return int(self.to01()[::-1], 2)

    def to_usb_buffer(self):
        """Return a USB packet byte array from a bit array."""

        # Create a temporary bit array from this bit array, but guaranteed to have multiple-of-8 number of bits.
        tmp = XsBitarray()
        tmp.frombytes(self.tobytes())
        # Reverse the bits within each byte of the bit array to correct for reversal in XESS USB firmware.
        tmp.bytereverse()
        return tmp.tobytes()

    def __setattr__(self, name, val):
        """Set the bit array from an integer, unsigned integer or string."""

        if name == 'unsigned' or name == 'int':
            self = XsBitarray.from_int(val, len(self))
        elif name == 'string':
            self = XsBitarray(val)
        return val

    def __getattr__(self, name):
        """Return the unsigned, integer or string representation of a bit array."""

        if name == 'int':
            val = self.to_int()
            # Correct for sign bit.
            if self[-1] == 1:
                val -= (1 << self.length())
        elif name == 'unsigned':
            # No need to correct for sign bit.
            val = self.to_int()
        elif name == 'string':
            val = self.to01()
        return val

Bitvec = XsBitarray # Associate old Bitvec class with new XsBitarray class.


if __name__ == '__main__':
    xsbits = XsBitarray('1010101')
    print str(xsbits)
    xsbits = XsBitarray.from_int(45)
    print str(xsbits)
    print xsbits.to01()
    print xsbits.to_int()
    xsbits = XsBitarray.from_int(27, 8)
    print str(xsbits)
    print xsbits.to_int()

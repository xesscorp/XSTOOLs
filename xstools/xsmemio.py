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
Class for reading and writing memory or registers in the FPGA
of an XESS board through the USB port.
"""

import logging
import itertools
from xshostio import *


class XsMemIo(XsHostIo):

    """Object for reading and writing memory or registers."""

    # Memory opcodes.
    _NOP_OPCODE   = XsBitArray('0b00')
    _READ_OPCODE  = XsBitArray('0b11')  # Read from memory.
    _WRITE_OPCODE = XsBitArray('0b10')  # Write to memory.
    _SIZE_OPCODE  = XsBitArray('0b01')  # Get the address and data widths of memory.
    _SIZE_RESULT_LENGTH = 16  # Length of _SIZE_OPCODE result.

    def __init__(
        self,
        xsusb_id=DEFAULT_XSUSB_ID,
        module_id=DEFAULT_MODULE_ID,
        xsjtag=None
        ):
        """Setup a DUT I/O object.
        
        xsusb_id = The ID for the USB port.
        module_id = The ID for the DUT I/O module in the FPGA.
        xsjtag = The Xsjtag USB port object. (Use this if not using xsusb_id.)
        """

        # Setup the super-class object.
        XsHostIo.__init__(self, xsjtag=xsjtag, xsusb_id=xsusb_id, module_id=module_id)

        # Get the number of inputs and outputs of the DUT.
        (self.address_width, self.data_width) = self._get_mem_widths()
        assert self.address_width != 0
        assert self.data_width != 0
        logging.debug('address width = ' + str(self.address_width))
        logging.debug('data width = ' + str(self.data_width))

    def _get_mem_widths(self):
        """Return the (address_width, data_width) of the memory."""

        SKIP_CYCLES = 1  # Skip cycles between issuing command and reading back result.

        # Send the opcode and then read back the bits with the memory's address and data width.
        params = self.send_rcv(payload=self._SIZE_OPCODE,
                               num_result_bits=self._SIZE_RESULT_LENGTH + SKIP_CYCLES)
        params.pop_field(SKIP_CYCLES)  # Remove the skipped cycles.

        # The address width is in the first half of the bit array.
        address_width = params.pop_field(self._SIZE_RESULT_LENGTH / 2).unsigned

        # The data width is in the last half of the bit array.
        data_width = params.pop_field(self._SIZE_RESULT_LENGTH / 2).unsigned
        return (address_width, data_width)

    def read(self, begin_address, num_of_reads=1):
        """Return a list of bit arrays read from memory.
        
        begin_address = memory address of first read.
        num_of_reads = number of memory reads to perform.
        """

        # Start the payload with the READ_OPCODE.
        payload = XsBitArray(self._READ_OPCODE)

        # Append the memory address to the payload.
        payload += XsBitArray(uint=begin_address, length=self.address_width)

        # Send the opcode and beginning address and then read back the memory data.
        # The number of values read back is one more than requested because the first value
        # returned is crap since the memory isn't ready to respond.
        result = self.send_rcv(payload=payload,
                               num_result_bits=self.data_width * (num_of_reads + 1))
        result.pop_field(self.data_width)  # Remove the first data value which is crap.

        if num_of_reads == 1:
            # Return the result bit array if there's only a single read.
            return result
        else:
            # Otherwise, return a list of bit arrays with data_width bits by partitioning the result bit array.
            results = []
            while result.len > 0:
                results.append(result.pop_field(self.data_width))
            return results

    def write(self, begin_address, data):
        """Write a list of bit arrays to the memory.
        
        begin_address = memory address of first write.
        data = list of bit arrays or integers.
        """

        # Start the payload with the WRITE_OPCODE.
        payload = XsBitArray(self._WRITE_OPCODE)

        # Append the memory address to the payload.
        payload += XsBitArray(uint=begin_address, length=self.address_width)

        # Concatenate the data to the payload.
        for d in data:
            if isinstance(d, XsBitArray):
                payload += d
            else:
                # Convert integers to bit arrays.
                payload += XsBitArray(uint=d, length=self.data_width)
        assert payload.len > self._WRITE_OPCODE.len

        # Send the payload to write the data to memory.
        self.send_rcv(payload=payload, num_result_bits=0)


XsMem = XsMemIo  # Associate the old XsMem class with the new XsMemIo class.

if __name__ == '__main__':
    import sys
    import random
    from bitarray import *
    from scipy import *
    from pylab import *


    def number_of_set_bits(i):
        return bitarray(bin(i)[2:]).count()


    def prng(curr, poly, mask):
        b = number_of_set_bits(curr & poly) & 1
        return ((curr << 1) | b) & mask


    print """
    ##################################################################
    # Get some random numbers from the RNG in the XuLA FPGA.
    ##################################################################
    """

    USB_ID = 0  # This is the USB index for the XuLA board connected to the host PC.
    RAND_ID = 1  # This is the identifier for the RNG in the FPGA.
    rand = XsMem(USB_ID, RAND_ID)  # Create an object for reading/writing the register.

    PERIOD = 2 ** rand.data_width  # Number of random numbers to read.
    rand.write(0, [0x80])
    rand_nums = rand.read(0, PERIOD)
    rand_nums = [XsBitArray(d).unsigned for d in rand_nums]

    prng_poly = (1 << 11) | (1 << 10) | (1 << 7) | (1 << 5)
    mask = (1 << rand.data_width) - 1
    py_rand_nums = [0] * PERIOD
    py_rand_nums[0] = 0x80
    for i in range(1, PERIOD):
        py_rand_nums[i] = prng(py_rand_nums[i - 1], prng_poly, mask)

    for i in range(1, PERIOD):
        print '%8x %8x' % (py_rand_nums[i], rand_nums[i - 1])

    compare = [rand_nums[i] != prng(rand_nums[i - 1], prng_poly, mask)
               for i in range(1, PERIOD)]
    if sum(compare) == 0:
        print '\nSUCCESS!'
    else:
        print '\n', sum(compare), 'ERRORS'

    hist(rand_nums, 40)
    show()

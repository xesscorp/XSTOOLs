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
import struct
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

    def read(self, begin_address, num_of_reads=1, return_type=XsBitArray()):
        """Return a list of bit arrays read from memory.
        
        begin_address = memory address of first read.
        num_of_reads = number of memory reads to perform.
        return_type = instance of the type of data to return. Negative integer=signed; positive integer=unsigned.
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

        if num_of_reads == 1: # Return the result bit array if there's only a single read.
            result.pop_field(self.data_width)  # Remove the first data value which is crap.
            if isinstance(return_type, XsBitArray):
                return result
            else:
                if return_type < 0:
                    return result.int
                else:
                    return result.uint
        else: # Otherwise, return a list of bit arrays with data_width bits by partitioning the result bit array.
            w = self.data_width
            l = result.length
            if isinstance(return_type, XsBitArray):
                # Chop the bit array into an array of smaller bit arrays.
                # Start from the far end, skip the first data value which is crap, and then proceed to the beginning.
                return [result[i:i+w] for i in range(l-2*w,-w,-w)]
            else: # Return type is not a bit array, so convert bit arrays into integers.
                try:
                    # If word width is not byte-sized, then raise exception and
                    # use the slower method.
                    if w % 8 != 0:
                        raise KeyError
                    # If word width is not 1, 2, 4 or 8 bytes wide, then an
                    # exception occurs and the slower method is used.
                    w_type = {1:'B', 2:'H', 4:'I', 8:'Q'}[w // 8]
                    if return_type < 0:
                        w_type = str.lower(w_type)
                    alignment = '>'
                    n_words = l // w  # Number of words in the bit array.
                    fmt = '{}{}{}'.format(alignment, n_words, w_type)
                    # Get bytes from bit array, form them into integers and reverse
                    # their order so index [0] corresponds to lowest memory address.
                    # (Skip first integer because it's crap.)
                    return struct.unpack(fmt, result.bytes)[-2::-1]
                except KeyError:
                    # Slower method:
                    #     Chop the bit array into an array of smaller bit arrays.
                    #     Start from the far end, skip the first data value 
                    #     which is crap, and then proceed to the beginning.
                    results = [result[i:i+w] for i in range(l-2*w,-w,-w)]
                    if return_type < 0 :
                        results = [d.int for d in results]
                    else:
                        results = [d.uint for d in results]
                    return results

    def write(self, begin_address, data, data_type=None):
        """Write a list of bit arrays to the memory.
        
        begin_address = memory address of first write.
        data = list of bit arrays or integers.
        data_type = instance of data that is stored in the data array. Negative integer=signed; positive integer=unsigned.
        """

        if data_type is None:
            if isinstance(data[0], XsBitArray):
                data_type = data[0]  # XsBitArray.
            else:
                data_type = 1  # Unsigned, positive integer.

        # Concatenate the data to the payload.
        if isinstance(data_type, XsBitArray):
            w = data_type.len
            payload = XsBitArray(w * len(data))
            index = w * (len(data)-1)
            for d in data:
                payload.overwrite(d, index)
                index -= w
        else:
            w = self.data_width
            l = len(data)
            if w % 8 == 0:
                words = [[(d>>i) & 0xff for i in range(0,w,8)] for d in data]
                bytes = [byte for word in words for byte in word]
                bytes.reverse()
                payload = BitArray(bytes=bytes)
            else:
                payload = XsBitArray(w * len(data))
                index = w * (len(data)-1)
                for d in data:
                    payload.overwrite(XsBitArray(uint=d, length=w), index)
                    index -= w

        # Start the payload with the WRITE_OPCODE.
        header = XsBitArray(self._WRITE_OPCODE)

        # Append the memory address to the payload.
        header += XsBitArray(uint=begin_address, length=self.address_width)
        
        payload = header + payload

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

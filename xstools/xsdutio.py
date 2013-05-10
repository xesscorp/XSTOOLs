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
Object for forcing inputs and reading outputs from a device-under-test (DUT).
"""

import logging
from xshostio import *


class XsDutIo(XsHostIo):

    """Object for forcing inputs and reading outputs from a device-under-test (DUT)."""

    # DUT opcodes.
    _NOP_OPCODE   = XsBitArray('0b00')
    _READ_OPCODE  = XsBitArray('0b11')  # Read DUT outputs.
    _WRITE_OPCODE = XsBitArray('0b10')  # Write to DUT inputs.
    _SIZE_OPCODE  = XsBitArray('0b01')  # Get number of inputs and outputs of DUT.
    _SIZE_RESULT_LENGTH = 16  # Length of _SIZE_OPCODE result.

    def __init__(
        self,
        xsusb_id=DEFAULT_XSUSB_ID,
        module_id=DEFAULT_MODULE_ID,
        dut_output_widths=None,
        dut_input_widths=None,
        xsjtag=None,
        ):
        """Setup a DUT I/O object.
        
        xsusb_id = The ID for the USB port.
        module_id = The ID for the DUT I/O module in the FPGA.
        dut_output_widths = A list of widths of the DUT output fields.
        dut_input_widths = A list of widths of the DUT input fields.
        xsjtag = The XsJtag USB port object. (Use this if not using xsusb_id.)
        """

        # Setup the super-class object.
        XsHostIo.__init__(self, xsusb_id=xsusb_id, module_id=module_id, xsjtag=xsjtag)
        # Get the number of inputs and outputs of the DUT.
        (self.total_dut_input_width, self.total_dut_output_width) = self._get_io_widths()
        assert self.total_dut_input_width != 0
        assert self.total_dut_output_width != 0
        logging.debug('# DUT input bits = %d' % self.total_dut_input_width)
        logging.debug('# DUT output bits = %d' % self.total_dut_output_width)

        if dut_input_widths == None:
            # If no DUT input widths are provided, then make a single-element
            # list containing just the total number of DUT input bits.
            self._dut_input_widths = [self.total_dut_input_width]
        elif isinstance(dut_input_widths, int):
            # Just a single input field, so make it into a list.
            self._dut_input_widths = [dut_input_widths]
        elif isinstance(dut_input_widths, list):
            # Otherwise, store the given list of DUT input field widths.
            self._dut_input_widths = dut_input_widths
            assert len(self._dut_input_widths) != 0
            # Total all the input field widths.
            total_width = 0
            for w in self._dut_input_widths:
                total_width += w
            # The total should equal the total number of DUT inputs.
            logging.debug('Total listed DUT input bits = %d' % total_width)
            assert total_width == self.total_dut_input_width
        else:
            raise XsMinorError('Unknown type of input width list.')
        if dut_output_widths == None:
            # If no DUT output widths are provided, then make a single-element
            # list containing just the total number of DUT output bits.
            self._dut_output_widths = [self.total_dut_output_width]
        elif isinstance(dut_output_widths, int):
            # Just a single output field, so make it into a list.
            self._dut_output_widths = [dut_output_widths]
        elif isinstance(dut_output_widths, list):
            # Otherwise, store the given list of DUT output field widths.
            self._dut_output_widths = dut_output_widths
            assert len(self._dut_output_widths) != 0
            # Total all the output field widths.
            total_width = 0
            for w in self._dut_output_widths:
                total_width += w
            # The total should equal the total number of DUT outputs.
            logging.debug('Total listed DUT output bits = %d' % total_width)
            assert total_width == self.total_dut_output_width
        else:
            raise XsMinorError('Unknown type of output width list.')

    def _get_io_widths(self):
        """Return the (total_dut_input_width, total_dut_output_width) of the DUT."""

        SKIP_CYCLES = 1  # Skip cycles between issuing command and reading back result.

        # Send the opcode and then read back the bits with the DUT's #inputs and #outputs.
        params = self.send_rcv(payload=self._SIZE_OPCODE,
                               num_result_bits=self._SIZE_RESULT_LENGTH + SKIP_CYCLES)
        params.pop_field(SKIP_CYCLES)  # Remove the skipped cycles.

        # The number of DUT inputs is in the first half of the bit array.
        total_dut_input_width = params.pop_field(self._SIZE_RESULT_LENGTH / 2).unsigned

        # The number of DUT outputs is in the last half of the bit array.
        total_dut_output_width = params.pop_field(self._SIZE_RESULT_LENGTH / 2).unsigned
        return (total_dut_input_width, total_dut_output_width)

    def read(self):
        """Return a list of bit arrays for the DUT output fields."""

        SKIP_CYCLES = 1  # Skip cycles between issuing command and reading back result.

        # Send the READ_OPCODE and then read back the bits with the DUT's output values.
        result = self.send_rcv(payload=self._READ_OPCODE,
                               num_result_bits=self.total_dut_output_width + SKIP_CYCLES)
        result.pop_field(SKIP_CYCLES)  # Remove the skipped cycles.
        assert result.len == self.total_dut_output_width
        logging.debug('Read result = ' + repr(result))

        if len(self._dut_output_widths) == 1:
            # Return the result bit array if there's only a single output field.
            return result
        else:
            # Otherwise, partition the result bit array into the given output field widths.
            outputs = []
            for w in self._dut_output_widths:
                outputs.append(result.pop_field(w))
            return outputs

    Read = read  # Associate the old Read() method with the new read() method.

    def write(self, *inputs):
        """Send a list of bit arrays to the DUT input fields."""

        # You need as many input bit arrays as there are input fields.
        assert len(inputs) == len(self._dut_input_widths)

        # Start the payload with the WRITE_OPCODE.
        payload = XsBitArray(self._WRITE_OPCODE[:])

        # Concatenate the DUT input field bit arrays to the payload.
        for (inp, width) in zip(inputs, self._dut_input_widths):
            if isinstance(inp, (int, bool)):
                # Convert the integer to a bit array and concatenate it.
                payload += XsBitArray(uint=inp, length=width)
            else:
                # Assume it's a bit array, so just concatenate it.
                payload += inp
        assert payload.len > self._WRITE_OPCODE.len

        # Send the payload to force the bit arrays onto the DUT inputs.
        self.send_rcv(payload=payload, num_result_bits=0)

    Write = write  # Associate the old Write() method with the new write() method.

    def execute(self, *inputs):
        """Send a list of bit arrays to the DUT input fields and get the DUT outputs."""

        self.write(*inputs)
        return self.read()

    Exec = execute  # Associate the old Exec() method with the new exec() method.


class XsDut(XsDutIo):

    def __init__(
        self,
        xsusb_id=DEFAULT_XSUSB_ID,
        module_id=DEFAULT_MODULE_ID,
        dut_input_widths=None,
        dut_output_widths=None,
        ):

        # The __init__ function of the old XsDut class had the argument positions of the input and output width lists reversed.
        XsDutIo.__init__(self, xsusb_id, module_id, dut_output_widths, dut_input_widths)


if __name__ == '__main__':

    #logging.root.setLevel(logging.DEBUG)

    from random import *  # Import some random number generator routines.

    USB_ID = 0  # USB port index for the XuLA board connected to the host PC.

    BLINKER_ID = 1  # This is the identifier for the blinker in the FPGA.
    SUBTRACTOR_ID = 4  # This is the identifier for the subtractor in the FPGA.

    # Create a blinker interface object that takes one 1-bit input and has one 1-bit output.
    blinker = XsDutIo(USB_ID, BLINKER_ID, [1], [1])

    # Create a subtractor intfc obj with two 8-bit inputs and one 8-bit output.
    subtractor = XsDutIo(USB_ID, SUBTRACTOR_ID, [8], [8, 8])

    # Test the subtractor by iterating through some random inputs.
    for i in range(0, 100):
        minuend = randint(0, 127)  # Get a random, positive byte...
        subtrahend = randint(0, 127)  # And subtract this random byte from it.
        diff = subtractor.Exec(minuend, subtrahend)  # Use the subtractor in FPGA.
        print '%3d - %3d = %4d' % (minuend, subtrahend, diff.int),
        if diff.int == minuend - subtrahend:  # Compare Python result to FPGA's.
            print '==> CORRECT!'  # Print this if the differences match.
        else:
            print '==> ERROR!!!'  # Oops! Something's wrong with the subtractor.
            
    blinker = 0
    blinker = XsDutIo(USB_ID, BLINKER_ID, [1], [1])

    while True: # Do this forever...
        led = blinker.Read() # Read the current state of the LED.
        print 'LED: %1d\r' % led.unsigned, # Print the LED state and return.
            
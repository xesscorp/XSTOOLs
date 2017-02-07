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
USB <=> JTAG port interface for an XESS FPGA board.
"""

import logging
from xserror import *
from xsbitarray import *
from xsusb import XsUsb


class XsJtag:

    """USB<=>JTAG port interface object for XESS FPGA board."""

    # Table that stores the next JTAG TAP state for a given TAP state and value of TMS.
    # Current TAP state : [Next TAP state if TMS=0, Next TAP state if TMS=1]
    _next_tap_state = {
        'Invalid': ['Invalid', 'Invalid'],
        'Test-Logic-Reset': ['Run-Test/Idle', 'Test-Logic-Reset'],
        'Run-Test/Idle': ['Run-Test/Idle', 'Select-DR-Scan'],
        'Select-DR-Scan': ['Capture-DR', 'Select-IR-Scan'],
        'Select-IR-Scan': ['Capture-IR', 'Test-Logic-Reset'],
        'Capture-DR': ['Shift-DR', 'Exit1-DR'],
        'Capture-IR': ['Shift-IR', 'Exit1-IR'],
        'Shift-DR': ['Shift-DR', 'Exit1-DR'],
        'Shift-IR': ['Shift-IR', 'Exit1-IR'],
        'Exit1-DR': ['Pause-DR', 'Update-DR'],
        'Exit1-IR': ['Pause-IR', 'Update-IR'],
        'Pause-DR': ['Pause-DR', 'Exit2-DR'],
        'Pause-IR': ['Pause-IR', 'Exit2-IR'],
        'Exit2-DR': ['Shift-DR', 'Update-DR'],
        'Exit2-IR': ['Shift-IR', 'Update-IR'],
        'Update-DR': ['Run-Test/Idle', 'Select-DR-Scan'],
        'Update-IR': ['Run-Test/Idle', 'Select-DR-Scan'],
        }

    def __init__(self, xsusb=None):
        """Initialize object."""

        self._xsusb = xsusb  # USB port to board.
        self._tap_state = 'Invalid'  # Start TAP FSM in undefined state.
        # Clear bit arrays that store TDI and TMS bits to be sent to board.
        self._tdi_bits = XsBitArray()
        self._tms_bits = XsBitArray()

    def _buffer_is_empty(self):
        """Return True if both TDI and TMS bit buffers are empty."""

        return self._tdi_bits.len == 0 and self._tms_bits.len == 0

    def shift_tms(self, tms):
        """Append the TMS bit to the TMS bit buffer and update the TAP state."""

        assert tms == 0 or tms == 0x01
        self._tms_bits += [tms]  # Append the bit to the buffer.
        logging.debug('Current TAP state = %s', self._tap_state)

        # Update the TAP state given the current state and the TMS bit value.
        self._tap_state = self._next_tap_state[self._tap_state][tms]
        logging.debug('New TAP state = %s', self._tap_state)

    def shift_tdi(self, tdi, do_exit_shift=False):
        """Append given bits to the TDI bit buffer.
        
        do_exit_shift = True if shift-ir or shift-dr state should be exited on last TDI bit.
        """

        # Flush any pending TMS bits before TDI bits are sent.
        if self._tms_bits.len > 0:
            self.flush()

        # TAP FSM must be in the shift-ir or shift-dr state if fetching TDO bits.
        assert self._tap_state == 'Shift-DR' or self._tap_state == 'Shift-IR'

        # Create a single-item bit array if just a single bit is being sent.
        if not isinstance(tdi, XsBitArray):
            tdi = XsBitArray([tdi])

        # Append the TDI bits to the end of the TDI buffer.
        self._tdi_bits += tdi
        if do_exit_shift:
            self.shift_tms(0x01)  # TMS=1 exits the shift-ir/dr state.
            self.flush()  # Flush everything to the JTAG port.
            assert self._tap_state == 'Exit1-IR' or self._tap_state == 'Exit1-DR'

    def shift_tdo(self, num_bits, do_exit_shift=False):
        """Return a bit array with a given number of bits from the TDO pin."""

        # It's an error to gather TDO bits if the USB port is not setup.
        assert self._xsusb is not None

        # Return empty array if no bits are requested.
        if num_bits == 0:
            return XsBitArray()

        # Flush any pending TMS/TDI bits before gathering TDO bits.
        self.flush()

        # TAP FSM must be in the shift-ir or shift-dr state if fetching TDO bits.
        assert self._tap_state == 'Shift-DR' or self._tap_state == 'Shift-IR'

        if do_exit_shift == True:
            # Get the first N-1 TDO bits before exiting the shift-ir/dr state.
            tdo_bits = self.shift_tdo(num_bits=num_bits - 0x01, do_exit_shift=False)
            # Now make TMS=1 to exit the shift-ir/dr state while getting the last TDO bit.
            self.shift_tms(0x01)  # Do this just to update the internal TAP state.
            self._tms_bits = XsBitArray()  # Then clear the TMS bit buffer.
            # Now get the final TDO bit and set TMS=1 to exit the shift-ir/dr state.
            cmd = self._make_jtag_cmd_hdr(num_bits=0x01, flags=XsUsb.GET_TDO_MASK | XsUsb.TMS_VAL_MASK)
            self._xsusb.write(cmd)  # Send the JTAG command with TMS=1.
            # Get the final TDO bit and put it on the end of the buffer.
            buffer = self._xsusb.read(0x01)
            tdo_bits += [buffer[0] & 0x01]
            assert self._tap_state == 'Exit1-IR' or self._tap_state == 'Exit1-DR'
        else:
            # Get the TDO bits but do not exit the shift-ir/dr state.
            cmd = self._make_jtag_cmd_hdr(num_bits=num_bits, flags=XsUsb.GET_TDO_MASK)
            self._xsusb.write(cmd)  # Send the JTAG command with TMS=0.
            # Now get a USB packet with enough bytes to hold all the requested bits.
            num_bytes = int((num_bits + 7) / 8)
            buffer = self._xsusb.read(num_bytes)
            # Turn the byte array into a bit array.
            tdo_bits = XsBitArray.from_usb(usb_bytes=buffer, length=num_bits)
            assert self._tap_state == 'Shift-IR' or self._tap_state == 'Shift-DR'
        logging.debug('shift_tdo TDO => %s', tdo_bits)
        return tdo_bits

    def _make_jtag_cmd_hdr(self, num_bits=0, flags=0):
        """Create the first six bytes of a JTAG_CMD command packet.
        num_bits = number of TDI/TDO/TMS bits in the packet.
        flags = JTAG_CMD flags OR'ed together.
        """

        # The command packet contains the JTAG_CMD byte and then the
        # number of bits as a 32-bit number starting with the least-significant byte
        # and then the flags byte.
        return bytearray([
            XsUsb.JTAG_CMD,
            num_bits & 0xff,
            num_bits >> 8 & 0xff,
            num_bits >> 16 & 0xff,
            num_bits >> 24 & 0xff,
            flags,
            ])

    def flush(self):
        """Flush the TDI/TMS buffers through the USB port."""

        # It's an error to flush if the USB port is not setup.
        assert self._xsusb is not None

        # Do nothing if the TMS/TDI buffers are empty.
        if self._buffer_is_empty():
            return

        if self._tdi_bits.len == 0:
            # No TDI bits to send, so just send the TMS bits.
            # Create the JTAG_CMD header for sending only the TMS bits.
            buffer = self._make_jtag_cmd_hdr(num_bits=self._tms_bits.len, flags=XsUsb.PUT_TMS_MASK)
            # Append the TMS bits (in byte array format) to the JTAG_CMD header.
            buffer.extend(self._tms_bits.to_usb())
        else:
            if self._tms_bits.len == 0:
                # No TMS bits to send, so just send the TDI bits.
                # Create the JTAG_CMD header for sending only the TDI bits.
                buffer = self._make_jtag_cmd_hdr(num_bits=self._tdi_bits.len, flags=XsUsb.PUT_TDI_MASK)
                # Append the TDI bits (in byte array format) to the JTAG_CMD header.
                buffer.extend(self._tdi_bits.to_usb())
            else:
                # Both TMS and TDI bits need to be sent.
                if self._tms_bits.len == self._tdi_bits.len:
                    # TDI and TMS bit buffers are equal in #bits.
                    # Create the JTAG_CMD header for sending both the TDI and TMS bits.
                    buffer = self._make_jtag_cmd_hdr(num_bits=self._tdi_bits.len, flags=XsUsb.PUT_TMS_MASK | XsUsb.PUT_TDI_MASK)
                    # Create byte arrays to hold the TDI and TMS bits for USB transfer.
                    tms_buffer = self._tms_bits.to_usb()
                    tdi_buffer = self._tdi_bits.to_usb()
                    # Create another byte array to hold the interleaved TDI and TMS buffers.
                    tms_tdi_buffer = bytearray(len(tms_buffer) + len(tdi_buffer))
                    # Interleave TMS and TDI bytes with the TMS bytes at even addresses...
                    tms_tdi_buffer[0::2] = tms_buffer
                    # ... and the TDI bytes at odd addresses.
                    tms_tdi_buffer[0x01::2] = tdi_buffer
                    # Append the TDI and TMS byte arrays to the JTAG_CMD header.
                    buffer.extend(tms_tdi_buffer)
                elif self._tms_bits.len == 0x01:
                    # There's multiple TDI bits but only one TMS bit.
                    # Remove the last TMS and TDI bits from the buffers.
                    last_tms_bit = self._tms_bits.tail(0x01)
                    self._tms_bits = self._tms_bits.head(self._tms_bits.len - 0x01)
                    last_tdi_bit = self._tdi_bits.tail(0x01)
                    self._tdi_bits = self._tdi_bits.head(self._tdi_bits.len - 0x01)
                    assert self._tms_bits.len == 0
                    assert self._tdi_bits.len != 0
                    # Now only TDI bits remain, so flush those.
                    self.flush()
                    # Now put the last TDI and TMS bits into the buffers and flush those.
                    self._tms_bits += [last_tms_bit]
                    self._tdi_bits += [last_tdi_bit]
                    self.flush()
                    return
                else:
                    # It's an error if we ever get here! That would mean there are
                    # both multiple TMS and TDI bits, but not the same number of each.
                    assert False

        # Send the JTAG_CMD packet with the attached TMS and/or TDI bits.
        self._xsusb.write(buffer)

        # Clear the TMS and TDI buffers.
        self._tms_bits = XsBitArray()
        self._tdi_bits = XsBitArray()

    def go_thru_tap_states(self, *states):
        """Go through a sequence of TAP states."""

        for next_state in states:
            assert next_state in self._next_tap_state, 'Illegal TAP state label: %s.' % next_state
            # Make sure the next TAP state is reachable from current state.
            assert next_state == self._next_tap_state[self._tap_state][0] or next_state == self._next_tap_state[self._tap_state][0x01]
            # Append the TMS bit that will move the TAP FSM to the desired state.
            self.shift_tms(next_state == self._next_tap_state[self._tap_state][0x01])

    def load_ir_then_dr(
        self,
        instruction=None,
        data=None,
        num_return_bits=0,
        ):
        """Load JTAG IR and then DR and return bits shifted out of DR.
        instruction = opcode for JTAG IR.
        data = bits to load into JTAG DR.
        num_return_bits = # of bits to shift out of DR.
        """

        # The TAP FSM should always start and return to the run-test/idle state until all instructions are done.
        if self._tap_state != 'Run-Test/Idle':
            self.reset_tap()
            self.go_thru_tap_states('Run-Test/Idle')

        if instruction != None:
            # Go  to the shift-ir state.
            self.go_thru_tap_states('Select-DR-Scan', 'Select-IR-Scan', 'Capture-IR', 'Shift-IR')
            # Now shift in the instruction opcode and activate it.
            self.shift_tdi(tdi=instruction, do_exit_shift=True)
            self.go_thru_tap_states('Update-IR')

        # TAP FSM can get to select-dr-scan from either of these states.
        assert self._tap_state == 'Run-Test/Idle' or self._tap_state == 'Update-IR'
        bits = XsBitArray()
        if data != None:
            # If there's data to send, then there should never be data to return.
            assert num_return_bits == 0
            # Go  to the shift-dr state.
            self.go_thru_tap_states('Select-DR-Scan', 'Capture-DR', 'Shift-DR')
            # Now shift in the data for the instruction.
            self.shift_tdi(tdi=data, do_exit_shift=True)
            self.go_thru_tap_states('Update-DR')
        elif num_return_bits != 0:
            # No data to send, but there is data to receive from the DR.
            self.go_thru_tap_states('Select-DR-Scan', 'Capture-DR', 'Shift-DR')
            # Shift the data out of the DR.
            bits = self.shift_tdo(num_bits=num_return_bits, do_exit_shift=True)
            self.go_thru_tap_states('Update-DR')
        assert self._tap_state == 'Run-Test/Idle' or self._tap_state == 'Update-IR' or self._tap_state == 'Update-DR'
        self.go_thru_tap_states('Run-Test/Idle')
        self.flush()
        return bits

    def reset_tap(self):
        """Reset the TAP FSM."""

        # Flush anything that's already in the buffer.
        self.flush()

        # Setting TMS=1 for five clocks guarantees TAP is in test-logic-reset state.
        for i in range(0, 5):
            self.shift_tms(0x01)
        self.flush()
        self._tap_state = 'Test-Logic-Reset'

    def run_test_idle(self):
        self.go_thru_tap_states('Run-Test/Idle')

    def runtest(self, num_tcks):
        """Clock the JTAG port a given number of times."""

        # Flush any TMS/TDI bits already in the buffer.
        self.flush()

        # The command packet contains the RUNTEST_CMD byte and then the
        # number of clocks as a 32-bit number starting with the least-significant byte.
        cmd = bytearray([XsUsb.RUNTEST_CMD, num_tcks & 0xff, num_tcks >> 8 & 0xff, num_tcks >> 16 & 0xff, num_tcks >> 24 & 0xff])
        self._xsusb.write(cmd)  # Send the command.

        # Check that the 1st byte of the command response matches the command opcode.
        if self._xsusb.read(5)[0] != XsUsb.RUNTEST_CMD:
            raise XsMajorError("Communication error with XESS board in 'runtest'.")


if __name__ == '__main__':
    logging.root.setLevel(logging.DEBUG)

    print '#XSUSB = %d' % XsUsb.get_num_xsusb()

    # Create an object for sending JTAG through the USB link.
    xsjtag = XsJtag(XsUsb())
    # Enter the IDCODE instruction into the JTAG IR and then receive 32 ID bits.
    idcode_instr = XsBitArray('0b001001')
    xsjtag.reset_tap()
    idcode = xsjtag.load_ir_then_dr(idcode_instr, None, 32)
    print 'idcode instruction = %s' % idcode_instr
    print 'idcode = %s' % idcode
    # Compare the ID code to the XC3S200A ID code.
    assert idcode.head(28) == XsBitArray('0b00000010001000011000000010010011').head(28)
    xsjtag.runtest(1000)
    print '\n***Test passed!***'

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
USB <=> JTAG port interface for an XESS FPGA board.
"""

import logging
from xsbitarray import *
from xsusb import XsUsb


class XsJtag:

    """USB<=>JTAG port interface object for XESS FPGA board."""

    # Table that stores the next JTAG TAP state for a given TAP state and value of TMS.
    # Current TAP state : [Next TAP state if TMS=0, Next TAP state if TMS=1]
    _next_tap_state = {
        'invalid_tap_state': ['invalid_tap_state', 'invalid_tap_state'
                              ],
        'test_logic_reset': ['run_test_idle', 'test_logic_reset'],
        'run_test_idle': ['run_test_idle', 'select_dr_scan'],
        'select_dr_scan': ['capture_dr', 'select_ir_scan'],
        'select_ir_scan': ['capture_ir', 'test_logic_reset'],
        'capture_dr': ['shift_dr', 'exit1_dr'],
        'capture_ir': ['shift_ir', 'exit1_ir'],
        'shift_dr': ['shift_dr', 'exit1_dr'],
        'shift_ir': ['shift_ir', 'exit1_ir'],
        'exit1_dr': ['pause_dr', 'update_dr'],
        'exit1_ir': ['pause_ir', 'update_ir'],
        'pause_dr': ['pause_dr', 'exit2_dr'],
        'pause_ir': ['pause_ir', 'exit2_ir'],
        'exit2_dr': ['shift_dr', 'update_dr'],
        'exit2_ir': ['shift_ir', 'update_ir'],
        'update_dr': ['run_test_idle', 'select_dr_scan'],
        'update_ir': ['run_test_idle', 'select_dr_scan'],
        }

    def __init__(self, xsusb=None):
        """Initialize object."""

        self._xsusb = xsusb  # USB port to board.
        self._tap_state = 'invalid_tap_state'  # Start TAP FSM in undefined state.
        # Clear bit arrays that store TDI and TMS bits to be sent to board.
        self._tdi_bits = XsBitarray()
        self._tms_bits = XsBitarray()

    def _buffer_is_empty(self):
        """Return True if both TDI and TMS bit buffers are empty."""

        return self._tdi_bits.length() == 0 and self._tms_bits.length() \
            == 0

    def go_thru_tap_states(self, states):
        """Go through a sequence of TAP states."""

        # TDI, TMS should have no pending transfers before changing TAP state.
        assert self._buffer_is_empty()
        for next_state in states:
            # Make sure the next TAP state is reachable from current state.
            assert next_state \
                == self._next_tap_state[self._tap_state][0] \
                or next_state \
                == self._next_tap_state[self._tap_state][0x01]
            # Append to the TMS buffer the bit that will cause movement of the TAP FSM
            # to the desired state.
            self.shift_tms(next_state
                           == self._next_tap_state[self._tap_state][0x01])
        self.flush()  # Flush the TMS bit buffer to the board.

    def shift_tms(self, tms):
        """Append the TMS bit to the TMS bit buffer and update the TAP state."""

        self._tms_bits.append(tms)  # Append the bit to the buffer.
        logging.debug('Current TAP state = ' + self._tap_state)
        # Update the TAP state given the current state and the TMS bit value.
        self._tap_state = self._next_tap_state[self._tap_state][tms]
        logging.debug('New TAP state = ' + self._tap_state)

    def shift_tdi(
        self,
        tdi,
        do_exit_shift=False,
        do_flush=True,
        ):
        """Append given bits to the TDI bit buffer.
        
        do_exit_shift = True if shift-ir or shift-dr state should be exited on last TDI bit.
        do_flush = True if bit buffers should be flushed after the given bits are appended.
        """

        # There should be no pending TMS bit transfers and the TAP FSM should be in
        # the shift-ir or shift-dr state if sending TDI bits.
        assert self._tms_bits.length() == 0
        assert self._tap_state == 'shift_dr' or self._tap_state \
            == 'shift_ir'
        # Create a single-item bit array if just a single bit is being sent.
        if type(tdi) != type(XsBitarray()):
            tdi = XsBitarray([tdi])
        # Append the TDI bits to the end of the TDI buffer.
        self._tdi_bits.extend(tdi)
        do_exit_shift and self.shift_tms(0x01)  # TMS=1 exits the shift-ir/dr state.
        do_flush and self.flush()

    def shift_tdo(self, num_bits, do_exit_shift=False):
        """Return a bit array with a given number of bits from the TDO pin."""

        if num_bits == 0:
            return XsBitarray()  # Return empty array if no bits are requested.

        # It's an error to gather TDO bits if the USB port is not setup.
        assert self._xsusb is not None
        # There should be no pending TMS or TDI bit transfers and the TAP FSM should be in
        # the shift-ir or shift-dr state if fetching TDO bits.
        assert self._buffer_is_empty()
        assert self._tap_state == 'shift_dr' or self._tap_state \
            == 'shift_ir'

        if do_exit_shift == True:
            # Get the first N-1 TDO bits before exiting the shift-ir/dr state.
            tdo_bits = self.shift_tdo(num_bits=num_bits - 0x01,
                    do_exit_shift=False)
            # Now make TMS=1 to exit the shift-ir/dr state while getting the last TDO bit.
            self.shift_tms(0x01)
            self._tms_bits = XsBitarray()
            # Now get the final TDO bit and set TMS=1 to exit the shift-ir/dr state.
            cmd = self._make_jtag_cmd_hdr(num_bits=0x01,
                    flags=XsUsb.GET_TDO_MASK | XsUsb.TMS_VAL_MASK)
            self._xsusb.write(cmd)  # Send the JTAG command with TMS=1.
            buffer = self._xsusb.read(0x01)  # Get the final TDO bit.
            tdo_bits.append(buffer[0] & 0x01)
        else:
            # Get the TDO bits but do not exit the shift-ir/dr state.
            cmd = self._make_jtag_cmd_hdr(num_bits=num_bits,
                    flags=XsUsb.GET_TDO_MASK)
            self._xsusb.write(cmd)  # Send the JTAG command with TMS=0.
            # Get a USB packet with enough bytes to hold all the requested bits.
            num_bytes = int((num_bits + 7) / 8)
            buffer = self._xsusb.read(num_bytes)
            # Turn the byte array into a bit array.
            bits = XsBitarray()
            bits.frombytes(buffer.tostring())
            # Received bytes have LSB at the MSB position, so reverse them.
            bits.bytereverse()
            # Remove any extra bits added at the end during the bytereverse() operation.
            tdo_bits = bits[:num_bits]
        return tdo_bits

    def reset_tap(self):
        """Reset the TAP FSM."""

        # It's an error to reset the TAP if the USB port is not setup.
        assert self._xsusb is not None
        # It's an error to reset the TAP FSM if TDI/TMS buffers have bits pending.
        assert self._buffer_is_empty()
        # Setting TMS=1 for five clocks guarantees TAP is in test-logic-reset state.
        for i in range(0, 5):
            self.shift_tms(0x01)
        self.flush()
        self._tap_state = 'test_logic_reset'

    def runtest(self, num_tcks):
        """Clock the JTAG port a given number of times."""

        # It's an error to clock if the USB port is not setup.
        assert self._xsusb is not None
        # The command packet contains the RUNTEST_CMD byte and then the
        # number of clocks as a 32-bit number starting with the least-significant byte.
        cmd = bytearray([XsUsb.RUNTEST_CMD, num_tcks & 0xff, num_tcks
                        >> 8 & 0xff, num_tcks >> 16 & 0xff, num_tcks
                        >> 24 & 0xff])
        self._xsusb.write(cmd)  # Send the command.
        response = self._xsusb.read(5)  # Get the command response.
        assert response[0] == XsUsb.RUNTEST_CMD  # 1st byte of response should match command opcode.

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
        # It's an error to flush if TMS/TDI buffers are empty.
        assert not self._buffer_is_empty()

        if self._tdi_bits.length() == 0:
            # No TDI bits to send, so just send the TMS bits.
            # Create the JTAG_CMD header for sending only the TMS bits.
            buffer = \
                self._make_jtag_cmd_hdr(num_bits=self._tms_bits.length(),
                    flags=XsUsb.PUT_TMS_MASK)
            # Append the TMS bits (in byte array format) to the JTAG_CMD header.
            buffer.extend(self._tms_bits.to_usb_buffer())
        else:
            if self._tms_bits.length() == 0:
                # No TMS bits to send, so just send the TDI bits.
                # Create the JTAG_CMD header for sending only the TDI bits.
                buffer = \
                    self._make_jtag_cmd_hdr(num_bits=self._tdi_bits.length(),
                        flags=XsUsb.PUT_TDI_MASK)
                # Append the TDI bits (in byte array format) to the JTAG_CMD header.
                buffer.extend(self._tdi_bits.to_usb_buffer())
            else:
                # Both TMS and TDI bits need to be sent.
                if self._tms_bits.length() == self._tdi_bits.length():
                    # TDI and TMS bit buffers are equal.
                    # Create the JTAG_CMD header for sending both the TDI and TMS bits.
                    buffer = \
                        self._make_jtag_cmd_hdr(num_bits=self._tdi_bits.length(),
                            flags=XsUsb.PUT_TMS_MASK
                            | XsUsb.PUT_TDI_MASK)
                    # Create byte arrays to hold the TDI and TMS bits for USB transfer.
                    tms_buffer = self._tms_bits.to_usb_buffer()
                    tdi_buffer = self._tdi_bits.to_usb_buffer()
                    # Create another byte array to hold the interleaved TDI and TMS buffers.
                    tms_tdi_buffer = bytearray(len(tms_buffer)
                            + len(tdi_buffer))
                    # Interleave TMS and TDI with TMS bytes at even addresses...
                    tms_tdi_buffer[0::2] = tms_buffer
                    # ... and TDI bytes at odd addresses.
                    tms_tdi_buffer[0x01::2] = tdi_buffer
                    # Append the TDI and TMS byte arrays to the JTAG_CMD header.
                    buffer.extend(tms_tdi_buffer)
                elif self._tms_bits.length() == 0x01:
                    # There's multiple TDI bits but only one TMS bit.
                    # Remove the last TMS and TDI bits from the buffers.
                    last_tms_bit = self._tms_bits.pop()
                    last_tdi_bit = self._tdi_bits.pop()
                    assert self._tms_bits.length() == 0
                    assert self._tdi_bits.length() != 0
                    # Now only TDI bits remain, so flush those.
                    self.flush()
                    # Now put the last TDI and TMS bits into the buffers and flush those.
                    self._tms_bits.append(last_tms_bit)
                    self._tdi_bits.append(last_tdi_bit)
                    self.flush()
                    return
                else:
                    # It's an error if we ever get here! That would mean there are
                    # both multiple TMS and TDI bits, but not the same number of each.
                    assert 0x01 == 0

        # Send the JTAG_CMD packet with the attached TMS and/or TDI bits.
        self._xsusb.write(buffer)
        # Clear the TMS and TDI buffers.
        self._tms_bits = XsBitarray()
        self._tdi_bits = XsBitarray()


if __name__ == '__main__':
    print '#XSUSB = %d' % XsUsb.get_num_xsusb()
    xsusb = XsUsb()
    xsjtag = XsJtag(xsusb)
    xsjtag.reset_tap()
    xsjtag.go_thru_tap_states(['run_test_idle', 'select_dr_scan',
                              'select_ir_scan', 'capture_ir', 'shift_ir'
                              ])

    idcode_instr = XsBitarray('001001'[::-0x01])
    xsjtag.shift_tdi(idcode_instr, do_exit_shift=True, do_flush=True)
    xsjtag.go_thru_tap_states(['update_ir', 'select_dr_scan',
                              'capture_dr', 'shift_dr'])

    idcode = xsjtag.shift_tdo(32, do_exit_shift=False)
    print idcode
    assert idcode[:28].to01()[::-0x01] == '0010001000011000000010010011'
    xsjtag.runtest(1000)
    print '\n***Test passed!***'

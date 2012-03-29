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
Xilinx FPGA objects - from generic to more-specific subclasses.
"""

import logging
import time
from xserror import *
from xsjtag import *
from xilbitstr import *


class XilinxFpga:

    """Generic Xilinx FPGA object."""

    def __init__(self, xsjtag=None):
        """Initialize the FPGA."""
        
        self.xsjtag = xsjtag

    def configure(self, bitstream=None):
        """Download the bitstream into the FPGA."""
        
        # String argument indicates a file name containing the bitstream, so read it in.
        if type(bitstream) is str:
            bitstream = XilinxBitstream(bitstream)
        # Abort if the FPGA doesn't match with the bitstream's target device type.
        if bitstream.device_type != self._DEVICE_TYPE:
            raise XsMinorError("Bitstream file doesn't match target device: %s != %s." 
                % (bitstream.device_type, self._DEVICE_TYPE))
        # Check the IDCODE of the physical FPGA to make sure it matches.
        # (Only check the first 28 bits. The last four are version bits.
        if self.get_idcode()[:28] != self._IDCODE[:28]:
            raise XsMinorError("FPGA IDCODE doesn't match the expected value (%s)." % self.get_idcode().string)
        # Start off configuration in the run-test/idle state.
        self.xsjtag.reset_tap()
        self.xsjtag.run_test_idle()
        # xapp139 -
        # http://www.xilinx.com/support/documentation/application_notes/xapp452.pdf
        # Must follow JPROGRAM with CFG_IN to keep device locked to JTAG.
        # See AR 16829.
        self.xsjtag.load_ir_then_dr(instruction=self._JPROGRAM_INSTR)
        self.xsjtag.load_ir_then_dr(instruction=self._CFG_IN_INSTR)
        # Give time for FPGA to clear its memory.
        time.sleep(0.001)
        # Now download the bitstream.
        self.xsjtag.load_ir_then_dr(instruction=self._CFG_IN_INSTR,
                data=bitstream.bits)
        # Bitstream downloaded, now startup the FPGA.
        self.xsjtag.load_ir_then_dr(instruction=self._JSTART_INSTR)
        self.xsjtag.runtest(num_tcks=12)
        self.xsjtag.load_ir_then_dr(instruction=self._JSTART_INSTR,
                data=XsBitarray(22))
        self.xsjtag.reset_tap()
        # Check to see if configuration was successful.
        if self.get_status()["DONE"] != True:
            raise XsMinorError("FPGA failed to configure (DONE=0).")

    def get_idcode(self):
        """Return the FPGA's 32-bit IDCODE."""
        
        # Enter the IDCODE instruction into the JTAG IR and then return the 32 ID bits.
        return self.xsjtag.load_ir_then_dr(instruction=self._IDCODE_INSTR,
                data=None, num_return_bits=32)

    def get_status(self):
        """Return dict containing the FPGA's status register bits."""
        
        # This is the command for reading the status register from UG332, pg 340.
        command = XsBitarray("1010101010011001")  # 0xaa99
        command.extend(XsBitarray("0010000000000000"))  # 0x2000
        command.extend(XsBitarray("0010100100000001"))  # 0x2901
        command.extend(XsBitarray("0010000000000000"))  # 0x2000
        command.extend(XsBitarray("0010000000000000"))  # 0x2000
        self.xsjtag.load_ir_then_dr(instruction=self._CFG_IN_INSTR,
                data=command)
        # Now read the 32 bits from the status register.
        status_bits = \
            self.xsjtag.load_ir_then_dr(instruction=self._CFG_OUT_INSTR,
                num_return_bits=32)
        status = {
            "SYNC_TIMEOUT": status_bits[15],
            "SEU_ERR": status_bits[14],
            "DONE": status_bits[13],
            "INIT": status_bits[12],
            "MODE": status_bits[9:12],
            "VSEL": status_bits[6:9],
            "GHIGH_B": status_bits[5],
            "GWE": status_bits[4],
            "GTS_CFG_B": status_bits[3],
            "DCM_LOCK": status_bits[2],
            "ID_ERROR": status_bits[1],
            "CRC_ERROR": status_bits[0],
            }
        return status


class Xc3sa(XilinxFpga):

    """Generic Xilinx Spartan-3A FPGA object."""

    # Spartan-3A JTAG instruction opcodes.
    _SAMPLE_INSTR = XsBitarray("000001"[::-1])
    _USER1_INSTR = XsBitarray("000010"[::-1])
    _USER2_INSTR = XsBitarray("000011"[::-1])
    _CFG_OUT_INSTR = XsBitarray("000100"[::-1])
    _CFG_IN_INSTR = XsBitarray("000101"[::-1])
    _INTEST_INSTR = XsBitarray("000111"[::-1])
    _USERCODE_INSTR = XsBitarray("001000"[::-1])
    _IDCODE_INSTR = XsBitarray("001001"[::-1])
    _HIGHZ_INSTR = XsBitarray("001010"[::-1])
    _JPROGRAM_INSTR = XsBitarray("001011"[::-1])
    _JSTART_INSTR = XsBitarray("001100"[::-1])
    _JSHUTDOWN_INSTR = XsBitarray("001101"[::-1])
    _EXTEST_INSTR = XsBitarray("001111"[::-1])
    _ISC_ENABLE_INSTR = XsBitarray("010000"[::-1])
    _ISC_PROGRAM_INSTR = XsBitarray("010001"[::-1])
    _ISC_NOOP_INSTR = XsBitarray("010100"[::-1])
    _ISC_READ_INSTR = XsBitarray("010101"[::-1])
    _ISC_DISABLE_INSTR = XsBitarray("010110"[::-1])
    _ISC_DNA_INSTR = XsBitarray("110001"[::-1])
    _BYPASS_INSTR = XsBitarray("111111"[::-1])

    def __init__(self, xsjtag=None):
        XilinxFpga.__init__(self, xsjtag=xsjtag)


class Xc3s50avq100(Xc3sa):

    """50 Kgate Spartan-3A FPGA in VQ100 package."""

    _DEVICE_TYPE = "3s50avq100"
    _IDCODE = XsBitarray("00000010001000010000000010010011"[::-1])

    def __init__(self, xsjtag=None):
        Xc3sa.__init__(self, xsjtag=xsjtag)


class Xc3s200avq100(Xc3sa):

    """200 Kgate Spartan-3A FPGA in VQ100 package."""

    _DEVICE_TYPE = "3s200avq100"
    _IDCODE = XsBitarray("00000010001000011000000010010011"[::-1])

    def __init__(self, xsjtag=None):
        Xc3sa.__init__(self, xsjtag=xsjtag)


if __name__ == "__main__":

    #logging.root.setLevel(logging.DEBUG)
    xsusb = XsUsb()
    xsjtag = XsJtag(xsusb)
    xc3s200a = Xc3s200avq100(xsjtag)
    print xc3s200a.get_idcode()
    if xc3s200a.get_idcode() != xc3s200a._IDCODE:
        print "ERROR"
    else:
        print "SUCCESS"

    print "Status =", xc3s200a.get_status()

    xsjtag.reset_tap()
    xsjtag.run_test_idle()
    xsusb.set_prog(1)
    xsusb.set_prog(0)
    xsusb.set_prog(1)
    time.sleep(0.03)

    print "Status =", xc3s200a.get_status()
    t = time.clock()
    xc3s200a.configure(bitstream="test_board_jtag.bit")
    t = time.clock() - t
    print "Time to download bitstream = %fs" % t
    print xc3s200a.get_status()

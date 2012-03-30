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
Classes for XESS XuLA board types.
"""

import time
from xserror import *
from xilfpga import *
from picmicro import *


class Xula:

    """Class object for a generic XuLA board."""

    def __init__(self, xsusb_id=0):
        self.xsusb = XsUsb(xsusb_id)
        self.xsjtag = XsJtag(self.xsusb)

    def reset(self):
        """Reset the XESS board."""

        xsusb.reset()

    def get_board_info(self):
        """Return XESS board information dictionary."""

        try:
            info = self.xsusb.get_info()
        except:
            self.reset()
        try:
            info = self.xsusb.get_info()
        except:
            raise XsMajorError('Unable to get XESS board information.')
        if sum(info) & 0xff != 0:
            raise XsMinorError('XESS board information is corrupted.')
        board = {}
        board['ID'] = '%02x%02x' % (info[1], info[2])
        board['VERSION'] = '%d.%d' % (info[3], info[4])
        # Description is 0-terminated string
        desc = info[5:-1]
        desc_len = desc.index(0)
        board['DESCRIPTION'] = desc[:desc_len].tostring()
        return board

    def configure(self, bitstream):
        """Configure the FPGA on the board with a bitstream."""

        # Clear any configuration already in the FPGA.
        self.xsusb.set_prog(1)
        self.xsusb.set_prog(0)
        self.xsusb.set_prog(1)
        time.sleep(0.03)  # Wait for FPGA to clear.
        # Configure the FPGA with the bitstream and return true if successful.
        self.fpga.configure(bitstream)

    def set_flags(self, boot, jtag):
        """Set nonvolatile flags controlling the XuLA behavior."""

        pass

    def update_firmware(self, hexfile):
        """Re-flash microcontroller with new firmware from hex file."""

        self.xsusb.enter_reflash_mode()
        self.micro.program_flash(hexfile)
        self.xsusb.enter_user_mode()

    def verify_firmware(self, hexfile):
        self.xsusb.enter_reflash_mode()
        self.micro.verify_flash(hexfile)
        self.xsusb.enter_user_mode()


class Xula50(Xula):

    """Class for a XuLA board with an XC3S50A FPGA."""

    def __init__(self, xsusb_id=0):
        Xula.__init__(self, xsusb_id)
        self.fpga = Xc3s50avq100(self.xsjtag)
        self.micro = Pic18f14k50(self.xsusb)


class Xula200(Xula):

    """Class for a XuLA board with an XC3S200A FPGA."""

    def __init__(self, xsusb_id=0):
        Xula.__init__(self, xsusb_id)
        self.fpga = Xc3s200avq100(self.xsjtag)
        self.micro = Pic18f14k50(self.xsusb)


# Add the previous class objects to the global dictionary of XESS board classes.
global xs_board_list
try:
    xs_board_list  # See if the dictionary already exists.
except:
    xs_board_list = {}  # Create dictionary if it doesn't exist.
xs_board_list['xula-50'] = {'BOARD_CLASS': Xula50}
xs_board_list['xula-200'] = {'BOARD_CLASS': Xula200}

if __name__ == '__main__':
    xula = Xula200(0)
    board_info = xula.get_board_info()
    print repr(board_info)
    xula.configure('test_board_jtag.bit')

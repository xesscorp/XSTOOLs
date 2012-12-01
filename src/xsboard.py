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
Classes for XESS FPGA board types.
"""

import time
import wx
import wx.lib.pubsub as PUBSUB
from xserror import *
from xilfpga import *
from xsdutio import *
from picmicro import *


class XsBoard:

    """Class object for a generic XESS FPGA board."""

    BASE_SIGNATURE = 0xA50000A5
    SELF_TEST_SIGNATURE = BASE_SIGNATURE | (1<<8)
    (TEST_START, TEST_WRITE, TEST_READ, TEST_DONE) = range(0,4)
    
    @classmethod
    def get_xsboard(cls, xsusb_id=0):
        xsboard = Xula50(xsusb_id)
        if xsboard.is_connected():
            return xsboard
        xsboard = Xula200(xsusb_id)
        if xsboard.is_connected():
            return xsboard
        xsboard = Xula2lx25(xsusb_id)
        if xsboard.is_connected():
            return xsboard
        return None

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
        
    def is_connected(self):
        return self.fpga.is_connected()
        
    def get_xsusb_id(self):
        return self.xsusb.get_xsusb_id()

    def configure(self, bitstream):
        """Configure the FPGA on the board with a bitstream."""

        try:
            PUBSUB.Publisher().sendMessage("Progress.Phase","Downloading bitstream")
            # Clear any configuration already in the FPGA.
            self.xsusb.set_prog(1)
            self.xsusb.set_prog(0)
            self.xsusb.set_prog(1)
            time.sleep(0.03)  # Wait for FPGA to clear.
            # Configure the FPGA with the bitstream.
            self.fpga.configure(bitstream)
            PUBSUB.Publisher().sendMessage("Progress.Phase","Download complete")
        except Exception as e:
            raise(e)

    def update_firmware(self, hexfile):
        """Re-flash microcontroller with new firmware from hex file."""

        try:
            PUBSUB.Publisher().sendMessage("Progress.Phase","Updating firmware")
            self.xsusb.enter_reflash_mode()
            self.micro.program_flash(hexfile)
            self.xsusb.enter_user_mode()
            PUBSUB.Publisher().sendMessage("Xsboard.Progress.Phase","Firmware update done")
        except Exception as e:
            raise(e)

    def verify_firmware(self, hexfile):
        self.xsusb.enter_reflash_mode()
        self.micro.verify_flash(hexfile)
        self.xsusb.enter_user_mode()
        
    def do_self_test(self, test_bitstream=None):
        """Load the FPGA with a bitstream to test the board and return true if the board passes."""

        try:
            if test_bitstream == None:
                test_bitstream = self.test_bitstream
            PUBSUB.Publisher().sendMessage("Progress.Phase","Downloading diagostic bitstream")
            self.configure(test_bitstream, silent=True)
            # Create a channel to query the results of the board test.
            dut = XsDutIo( dut_output_widths=[2,1,32], dut_input_widths=1, xsjtag=self.xsjtag)
            # Assert and release the reset for the testing circuit.
            dut.write(1)
            dut.write(0)
            PUBSUB.Publisher().sendMessage("Progress.Phase","Writing SDRAM")
            prev_progress = XsBoard.TEST_START
            while True:
                [progress, failed, signature] = dut.read()
                if signature.unsigned != XsBoard.SELF_TEST_SIGNATURE:
                    raise XsMajorError("Self-test bitstream is not present.")
                if progress.unsigned != prev_progress:
                    if progress.unsigned == XsBoard.TEST_READ:
                        PUBSUB.Publisher().sendMessage("Progress.Phase","Reading SDRAM")
                    if failed.unsigned == 1:
                        PUBSUB.Publisher().sendMessage("Xsboard.Progress.Phase","Test Done")
                        raise XsMinorError("Board failed diagnostic.")
                    elif progress.unsigned == XsBoard.TEST_DONE:
                        PUBSUB.Publisher().sendMessage("Xsboard.Progress.Phase","Test Done")
                        return # Test passed!
                prev_progress = progress.unsigned
        except Exception as e:
            raise(e)
        
        
class Xula(XsBoard):

    """Class for a generic XuLA board."""
    
    name = "XuLA"
    dir = "xula/"

    def set_flags(self, boot, jtag):
        """Set nonvolatile flags controlling the XuLA behavior."""

        pass
        


class Xula50(Xula):

    """Class for a XuLA board with an XC3S50A FPGA."""
    
    name = Xula.name + "-50"
    dir = Xula.dir + "50/usb/"
    test_bitstream = dir + "test_board_jtag.bit"

    def __init__(self, xsusb_id=0):
        Xula.__init__(self, xsusb_id)
        self.fpga = Xc3s50avq100(self.xsjtag)
        self.micro = Pic18f14k50(self.xsusb)


class Xula200(Xula):

    """Class for a XuLA board with an XC3S200A FPGA."""

    name = Xula.name + "-200"
    dir = Xula.dir + "200/usb/"
    test_bitstream = dir + "test_board_jtag.bit"

    def __init__(self, xsusb_id=0):
        Xula.__init__(self, xsusb_id)
        self.fpga = Xc3s200avq100(self.xsjtag)
        self.micro = Pic18f14k50(self.xsusb)

class Xula2(Xula):
    """Class for generic XuLA2 board."""
    
    name = "XuLA2"
    dir = "xula2/"
    pass
    
class Xula2lx25(Xula2):
    """Class for a XuLA2 board with an XC6SLX25 FPGA."""

    name = Xula2.name + "-LX25"
    dir = Xula2.dir + "lx25/usb/"
    test_bitstream = dir + "test_board_jtag.bit"
    
    def __init__(self, xsusb_id=0):
        Xula2.__init__(self, xsusb_id)
        self.fpga = Xc6slx25ftg256(self.xsjtag)
        self.micro = Pic18f14k50(self.xsusb)


global xs_board_list
try:
    xs_board_list  # See if the dictionary already exists.
except:
    xs_board_list = {}  # Create dictionary if it doesn't exist.
xs_board_list['xula-50'] = {'BOARD_CLASS': Xula50, 'TEST_BITSTREAM':'test_board_jtag.bit'}
xs_board_list['xula-200'] = {'BOARD_CLASS': Xula200, 'TEST_BITSTREAM':'test_board_jtag.bit'}
xs_board_list['xula2-lx25'] = {'BOARD_CLASS': Xula2lx25, 'TEST_BITSTREAM':'test_board_jtag.bit'}

if __name__ == '__main__':
    xula = Xula200(0)
    board_info = xula.get_board_info()
    print repr(board_info)
    xula.configure('test_board_jtag.bit')

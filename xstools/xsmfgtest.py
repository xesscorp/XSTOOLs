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
This command-line program allows you to reprogram the flash memory in the
microcontroller and test the XESS board.

You would reprogram the microcontroller flash and test as follows:

    xsmfgtest -f program.hex
    
which writes the contents of the program.hex file into the PIC uC on
the board attached to the USB port and then runs the diagnostic
bitstream. For more info on using this program, type xsmfgtest -h.
"""

try:
    import winsound
except ImportError:
    pass

import sys
import time
import string
import logging
from argparse import ArgumentParser
import xsboard as XSBOARD
import xserror as XSERROR
from __init__ import __version__

def xsmfgtest():
    p = ArgumentParser(description='Program a firmware hex file into the uC and then test the XESS board.')
    p.add_argument('-f', '--filename', type=str, required=True, metavar='FILE.HEX', help='The name of the firmware hex file.')
    p.add_argument('-l', '--logfile', type=str, default='./xsusbprg.log', metavar='FILE.LOG',
                   help='Name of the log file to fill with all the nasty output for debugging and tracing what this program is doing: [%(default)s]'
                   )
    p.add_argument('-u', '--usb', type=int, default=0, metavar='N',
                   help='The USB port number for the XESS board. If you only have one board, then use 0.'
                   )
    p.add_argument('-b', '--board', type=str, default='xula-200', metavar='BOARD_NAME',
                   help='***DEPRECATED*** The XESS board type (e.g., xula2-lx9)')
    p.add_argument('-m', '--multiple', action='store_const', const=True,
                   default=False, help='Program multiple boards whenever a board is detected on the USB port.')
    p.add_argument('--verify', action='store_const', const=True,
                   default=False,
                   help='Verify the microcontroller flash against the firmware hex file.'
                   )
    p.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__,
                   help='Print the version number of this program and exit.'
                   )
    args = p.parse_args()

    args.board = string.lower(args.board)

    try:
        while True:
            num_boards = XSBOARD.XsUsb.get_num_xsusb()
            while num_boards == 0:
                num_boards = XSBOARD.XsUsb.get_num_xsusb()
            xs_board = XSBOARD.XsBoard.get_xsboard(args.usb)
            if xs_board is None:
                raise XsFatalError('No XESS Board at USB{}.'.format(args.usb))
            if args.verify == True:
                print 'Verifying microcontroller firmware against %s.' % args.filename
                xs_board.verify_firmware(args.filename)
                print 'Verification passed!'
            else:
                print 'Programming microcontroller firmware with %s.' % args.filename
                xs_board.update_firmware(args.filename)
                print 'Programming complete!'
            try:
                xs_board = XSBOARD.XsBoard.get_xsboard(args.usb)
                xs_board.do_self_test()
                print "Success:", xs_board.name, "passed diagnostic test!"
                try:
                    winsound.MessageBeep()
                except:
                    pass
            except XSERROR.XsError as e:
                try:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                except:
                    pass
            xs_board.xsusb.disconnect()
            while XSBOARD.XsUsb.get_num_xsusb() != 0:
                pass
    except XSERROR.XsError:
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        time.sleep(0.5)
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        raise XsFatalError('Program terminated abnormally.')
        exit()


if __name__ == '__main__':
    xsmfgtest()

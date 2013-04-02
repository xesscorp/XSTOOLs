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
microcontroller that manages the USB interface of an XESS board.

You would reprogram the microcontroller flash as follows:

    xsusbprg -f program.hex
    
which write the contents of the program.hex file into the PIC uC on
the XuLA-200 board attached to a USB port. For more info on using this
program, type xsusbprg -h.

This program was originally conceived and coded in C++ by Dave Vandenbout.
Al Neissner re-wrote it in python. Dave then took ideas and bits of Al's 
code and integrated them into this program and the XSTOOLs classes and methods.
"""

try:
    import winsound
except ImportError:
    pass

import string
from argparse import ArgumentParser
import xstools.xsboard as XSBOARD
import xstools.xserror as XSERROR

VERSION = '6.0.2'

p = ArgumentParser(description='Program a firmware hex file into the microcontroller on an XESS board.')
    
p.add_argument('-f', '--filename', type=str, required=True,
               help='The name of the firmware hex file.')
p.add_argument('-u', '--usb', type=int, default=0,
               help='The USB port number for the XESS board. If you only have one board, then use 0.')
p.add_argument('-b', '--board', type=str, default='xula-200',
               help='***DEPRECATED*** The XESS board type (e.g., xula-200)')
p.add_argument('-m', '--multiple', action='store_const', const=True,
               default=False, help='Program multiple boards each time a board is detected on the USB port.')
p.add_argument('--verify', action='store_const', const=True, default=False,
               help='Verify the microcontroller flash against the firmware hex file.')
p.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION,
               help='Print the version number of this program and exit.')
args = p.parse_args()

args.board = string.lower(args.board)

while(True):
    num_boards = XSBOARD.XsUsb.get_num_xsusb()
    if num_boards > 0:
        if 0 <= args.usb < num_boards:
            xs_board = XSBOARD.XsBoard.get_xsboard(args.usb)
            try:
                if args.verify == True:
                    print 'Verifying microcontroller firmware against %s.' % args.filename
                    xs_board.verify_firmware(args.filename)
                    print 'Verification passed!'
                else:
                    print 'Programming microcontroller firmware with %s.' % args.filename
                    xs_board.update_firmware(args.filename)
                    print 'Programming complete!'
            except XSERROR.XsError as e:
                try:
                    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                except:
                    pass
                xs_board.xsusb.disconnect()
                if args.multiple:
                    while XSBOARD.XsUsb.get_num_xsusb() != 0:
                        pass
                    continue
                else:
                    exit()
            try:
                winsound.MessageBeep()
            except:
                pass
            xs_board.xsusb.disconnect()
            if args.multiple:
                while XSBOARD.XsUsb.get_num_xsusb() != 0:
                    pass
                continue
            else:
                exit()
        else:
            XSERROR.XsFatalError( "%d is not within USB port range [0,%d]" % (args.usb, num_boards-1))
            exit()
    elif not args.multiple:
        XSERROR.XsFatalError("No XESS Boards found!")
        exit()
exit()

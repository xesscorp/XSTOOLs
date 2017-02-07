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

import sys
import os
import string
from argparse import ArgumentParser
import xsboard as XSBOARD
import xserror as XSERROR
from __init__ import __version__

SUCCESS = 0
FAILURE = 1


def xsusbprg():

    try:
        num_boards = XSBOARD.XsUsb.get_num_xsusb()

        p = ArgumentParser(
            description=
            'Program a firmware hex file into the microcontroller on an XESS board.')

        p.add_argument(
            '-f', '--filename',
            type=str,
            default=None,
            metavar='FILE.HEX',
            help='The name of the firmware hex file.')
        p.add_argument(
            '-u', '--usb',
            type=int,
            default=0,
            choices=range(num_boards),
            help=
            'The USB port number for the XESS board. If you only have one board, then use 0.')
        p.add_argument(
            '-b', '--board',
            type=str.lower,
            default='none',
            choices=['xula-50', 'xula-200', 'xula2-lx9', 'xula2-lx25'])
        p.add_argument(
            '-m', '--multiple',
            action='store_const',
            const=True,
            default=False,
            help=
            'Program multiple boards each time a board is detected on the USB port.')
        p.add_argument(
            '--verify',
            action='store_const',
            const=True,
            default=False,
            help=
            'Verify the microcontroller flash against the firmware hex file.')
        p.add_argument(
            '-v', '--version',
            action='version',
            version='%(prog)s ' + __version__,
            help='Print the version number of this program and exit.')
            
        args = p.parse_args()

        while (True):
            if num_boards > 0:
                xs_board = XSBOARD.XsBoard.get_xsboard(args.usb, args.board)
                try:
                    if args.verify == True:
                        print 'Verifying microcontroller firmware against %s.' % args.filename
                        xs_board.verify_firmware(args.filename)
                        print 'Verification passed!'
                    else:
                        print 'Programming microcontroller firmware with %s.' % args.filename
                        xs_board.update_firmware(args.filename)
                        print 'Programming completed!'
                except XSERROR.XsError as e:
                    try:
                        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                    except:
                        pass
                    if args.multiple:
                        xs_board.xsusb.disconnect()
                        while XSBOARD.XsUsb.get_num_xsusb() != 0:
                            pass
                        continue
                    else:
                        sys.exit(FAILURE)
                try:
                    winsound.MessageBeep()
                except:
                    pass
                if args.multiple:
                    xs_board.xsusb.disconnect()
                    while XSBOARD.XsUsb.get_num_xsusb() != 0:
                        pass
                    continue
                else:
                    sys.exit(SUCCESS)
                    
            elif not args.multiple:
                XSERROR.XsFatalError("No XESS Boards found!")

    except SystemExit as e:
        os._exit(SUCCESS)


if __name__ == '__main__':
    xsusbprg()

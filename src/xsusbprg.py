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

    xsusbprg -f program.hex -b xula-200
    
which write the contents of the program.hex file into the PIC uC on
the XuLA-200 board attached to a USB port. For more info on using this
program, type xsusbprg -h.

This program was originally conceived and coded in C++ by Dave Vandenbout.
Al Neissner re-wrote it in python. Dave then took ideas and bits of Al's 
code and integrated them into this program and the XSTOOLs classes and methods.
"""

from argparse import ArgumentParser
import logging
from xula import *
from xserror import *

VERSION = '2.0.0'

p = \
    ArgumentParser(description='Program a firmware hex file into the microcontroller on an XESS board.'
                   )
p.add_argument('-f', '--filename', type=str, required=True,
               help='The name of the firmware hex file.')
p.add_argument('-l', '--logfile', type=str, default='./xsusbprg.log',
               help='Name of the log file to fill with all the nasty output for debugging and tracing what this program is doing: [%(default)s]'
               )
p.add_argument('-u', '--usb', type=int, default=0,
               help='The USB port number for the XESS board. If you only have one board, then use 0.'
               )
p.add_argument('-b', '--board', type=str, default='xula-200',
               help='The XESS board type (e.g., xula-200)')
p.add_argument('-m', '--multiple', action='store_const', const=True,
               default=False, help='Program multiple boards whenever a board is detected on the USB port.')
p.add_argument('--verify', action='store_const', const=True,
               default=False,
               help='Verify the microcontroller flash against the firmware hex file.'
               )
p.add_argument('-v', '--version', action='version', version='%(prog)s '
               + VERSION,
               help='Print the version number of this program and exit.'
               )
args = p.parse_args()

args.board = string.lower(args.board)

try:
    while True:
        while XsUsb.get_num_xsusb() == 0:
            pass
        if args.board in xs_board_list:
            xs_board = xs_board_list[args.board]['BOARD_CLASS'](args.usb)
        else:
            raise XsMinorError("Unknown XESS board type '%s'." % args.board)
        if args.verify == True:
            print 'Verifying microcontroller firmware against %s.' \
                % args.filename
            xs_board.verify_firmware(args.filename)
            print 'Verification passed!'
        else:
            print 'Programming microcontroller firmware with %s.' \
                % args.filename
            xs_board.update_firmware(args.filename)
            print 'Programming complete!'
        if args.multiple == False:
            break
        while XsUsb.get_num_xsusb() != 0:
            pass
except XsError:
    raise XsFatalError('Program terminated abnormally.')
    exit()

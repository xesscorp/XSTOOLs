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
This command-line program runs a self-test on an XESS board like so:

    xstest -b xula-200
    
which downloads a self-test bitstream into a XuLA-200 board
attached to a USB port and reports the result. For more info on 
using this program, type xsload -h.

This program was originally conceived and written in C++ by Dave 
Vandenbout and then ported to python.
"""

import winsound
from argparse import ArgumentParser
import logging
from xula import *
from xserror import *

VERSION = '6.0.0'

p = \
    ArgumentParser(description='Run self-test on an XESS board.'
                   )
p.add_argument('-l', '--logfile', type=str, default='./xsload.log',
               help='Name of the log file to fill with all the nasty output for debugging and tracing what this program is doing: [%(default)s]'
               )
p.add_argument('-u', '--usb', type=int, default=0,
               help='The USB port number for the XESS board. If you only have one board, then use 0.'
               )
p.add_argument('-b', '--board', type=str, default='xula-200',
               help='The XESS board type (e.g., xula-200)')
p.add_argument('-m', '--multiple', action='store_const', const=True,
               default=False, help='Run the self-test each time a board is detected on the USB port.')
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
            xs_board = xs_board_list[args.board]['BOARD_CLASS'
                    ](xsusb_id=args.usb)
        else:
            raise XsMinorError("Unknown XESS board type '%s'." % args.board)
        if xs_board.do_self_test(xs_board_list[args.board]['TEST_BITSTREAM']) == True:
            print "Board is OK!"
            winsound.MessageBeep()
        else:
            print "Board failed!"
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        xs_board.xsusb.disconnect()
        if args.multiple == False:
            break
        while XsUsb.get_num_xsusb() != 0:
            pass
except XsError:
    raise XsFatalError('Program terminated abnormally.')
    exit()

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
This command-line program downloads a bitstream into the FPGA
on an XESS board.

The most common use of this program is to download a bitstream into an 
XESS board like so:

    xsload -f design.bit -b xula-200
    
which downloads the bitstream in design.bit into the XuLA-200 board
attached to a USB port. For more info on using this program, type
xsload -h.

This program was originally conceived and written in C++ by Dave 
Vandenbout. James Bowman ported it to python. Hector Peraza 
modified the python code to eliminate some problems and make 
FPGA configuration via JTAG conform to accepted practice.
Dave took ideas and bits of Hector's code and integrated them 
into this program and the XSTOOLs classes and methods.
"""

import sys
import string
from argparse import ArgumentParser
import xstools.xsboard as XSBOARD
import xstools.xserror as XSERROR
from xstools_defs import *

p = ArgumentParser(description='Program a bitstream file into the FPGA on an XESS board.')

p.add_argument('--fpga', type=str, 
               help='The name of the bitstream file to load into the FPGA.')
p.add_argument('--flash', type=str, 
               help='The name of the file to down/upload to/from the serial configuration flash.')
p.add_argument('--ram', type=str, 
               help='The name of the file to down/upload to/from the RAM.')
p.add_argument('-u', '--upload', nargs=2, type=int, default=0,
               help='Upload from RAM or flash the data between the lower and upper addresses.')
p.add_argument('--usb', type=int, default=0,
               help='The USB port number for the XESS board. If you only have one board, then use 0.')
p.add_argument('-b', '--board', type=str, default='xula-200',
               help='***DEPRECATED*** The XESS board type (e.g., xula-200)')
p.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION,
               help='Print the version number of this program and exit.')
args = p.parse_args()

args.board = string.lower(args.board)
    
num_boards = XSBOARD.XsUsb.get_num_xsusb()
if num_boards > 0:
    if 0 <= args.usb < num_boards:
        xs_board = XSBOARD.XsBoard.get_xsboard(args.usb)
            
        if args.flash:
            if args.upload:
                hexfile_data = xs_board.read_cfg_flash(bottom=args.upload[0], top=args.upload[1])
                hexfile_data.tofile(args.flash, format='hex')
            else:
                xs_board.write_cfg_flash(args.flash)

        if args.fpga:
            try:
                xs_board.configure(args.fpga)
            except XSERROR.XsError as e:
                xs_board.xsusb.disconnect()
                sys.exit()
            print "Success: Bitstream", args.fpga, "downloaded into", xs_board.name, "!"
                
        xs_board.xsusb.disconnect()
        sys.exit()
    else:
        XSERROR.XsFatalError( "%d is not within USB port range [0,%d]" % (args.usb, num_boards-1))
        sys.exit()
else:
    XSERROR.XsFatalError("No XESS Boards found!")
    sys.exit()

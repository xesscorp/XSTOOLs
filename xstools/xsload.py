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

import os
import sys
import string
from argparse import ArgumentParser
import xsboard as XSBOARD
import xserror as XSERROR
from __init__ import __version__

SUCCESS = 0
FAILURE = 1


def xsload():

    try:
        num_boards = XSBOARD.XsUsb.get_num_xsusb()

        p = ArgumentParser(
            description=
            'Program a bitstream file into the FPGA on an XESS board.')

        p.add_argument(
            '--fpga',
            type=str,
            metavar='FILE.BIT',
            help='The name of the bitstream file to load into the FPGA.')
        p.add_argument(
            '--flash',
            type=str,
            metavar='FILE.HEX',
            help=
            'The name of the file to down/upload to/from the serial configuration flash.')
        p.add_argument(
            '--ram',
            type=str,
            metavar='FILE.HEX',
            help='The name of the file to down/upload to/from the RAM.')
        p.add_argument(
            '-u', '--upload',
            nargs=2,
            type=int,
            default=0,
            metavar=('LOWER', 'UPPER'),
            help=
            'Upload from RAM or flash the data between the lower and upper addresses.')
        p.add_argument(
            '--usb',
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
            '-v', '--version',
            action='version',
            version='%(prog)s ' + __version__,
            help='Print the version number of this program and exit.')

        args = p.parse_args()

        if num_boards > 0:
            xs_board = XSBOARD.XsBoard.get_xsboard(args.usb, args.board)

            if args.flash:
                try:
                    if args.upload:
                        hexfile_data = xs_board.read_cfg_flash(
                            bottom=args.upload[0],
                            top=args.upload[1])
                        hexfile_data.tofile(args.flash, format='hex')
                        print "Success: Data in address range [{bottom},{top}] of serial flash on {board} uploaded to {file}!".format(
                            bottom=args.upload[0],
                            top=args.upload[1],
                            board=xs_board.name,
                            file=args.flash)
                    else:
                        xs_board.write_cfg_flash(args.flash)
                        print "Success: Data in {file} downloaded to serial flash on {board}!".format(
                            file=args.flash,
                            board=xs_board.name)
                except XSERROR.XsError as e:
                    sys.exit(FAILURE)

            if args.ram:
                try:
                    if args.upload:
                        hexfile_data = xs_board.read_sdram(
                            bottom=args.upload[0],
                            top=args.upload[1])
                        hexfile_data.tofile(args.ram, format='hex')
                        print "Success: Data in address range [{bottom},{top}] of RAM on {board} uploaded to {file}!".format(
                            bottom=args.upload[0],
                            top=args.upload[1],
                            board=xs_board.name,
                            file=args.ram)
                    else:
                        xs_board.write_sdram(args.ram)
                        print "Success: Data in {file} downloaded to RAM on {board}!".format(
                            file=args.flash,
                            board=xs_board.name)
                except XSERROR.XsError as e:
                    sys.exit(FAILURE)

            if args.fpga:
                try:
                    xs_board.configure(args.fpga)
                    print "Success: Bitstream in {file} downloaded to FPGA on {board}!".format(
                        file=args.fpga, 
                        board=xs_board.name)
                except XSERROR.XsError as e:
                    sys.exit(FAILURE)

            sys.exit(SUCCESS)
        else:
            XSERROR.XsFatalError("No XESS Boards found!")

    except SystemExit as e:
        os._exit(SUCCESS)


if __name__ == '__main__':
    xsload()

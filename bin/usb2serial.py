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
#   (c)2014 - X Engineering Software Systems Corp. (www.xess.com)
# **********************************************************************

"""
This command-line program is a server that transfers bytes between
a COM/serial port and the USB port of a XuLA board.
"""

import sys

# Use local development version of xstools when use_local_xstools.py exists.
# Remember to delete both use_local_xstools.py and use_local_xstools.pyc.
try:
    import use_local_xstools
except:
    pass
else:
    sys.path.insert(0, r'..')

import serial
import string
import logging
from argparse import ArgumentParser
import xstools.xsboard as XSBOARD
import xstools.xserror as XSERROR
import xstools.xscomm as XSCOMM
import xstools.xsdutio as XSDUTIO
from xstools_defs import *
import time

p = ArgumentParser(description='Transfer bytes between a COM/serial port and the USB port of a XuLA board.')

p.add_argument('-c', '--comport', type=int, default=1,
               help='The COM port number.')
p.add_argument('-u', '--usb', type=int, default=0,
               help='The USB port number for the XESS XuLA board. If you only have one board, then use 0.')
p.add_argument('-m', '--module', type=int, default=253,
               help='The ID of the comm module in the XuLA attached to the USB port.')
p.add_argument('-d', '--debug', action='store_true',
               help='Turn on debugging messages.')
p.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION,
               help='Print the version number of this program and exit.')
args = p.parse_args()

logger = logging.getLogger('USB<=>serial')
if args.debug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(1000)

xsreset = XSDUTIO.XsDutIo(xsusb_id=args.usb, module_id=254, dut_input_widths=[1])
xsreset.write(1)
xscomm = XSCOMM.XsComm(xsusb_id=args.usb, module_id=args.module)
xscomm.get_levels()
#xscomm.reset()

sercomm = serial.Serial(args.comport - 1)
sercomm.writeTimeout = 0  # This disables serial port write timeouts. Don't use 'None'.
print "Serial port = ", sercomm.name

break_pattern = [0x00, 0xFF, 0x00]  # Serial data pattern indicating break signal.
break_buf = [0x11 for i in range(len(break_pattern))]  # Initialize with garbage.
def break_found(buf):
    '''Detect a break pattern in the serial data stream.'''
    global break_buf
    for b in buf:
        break_buf.append(b)
        break_buf = break_buf[1:]
        if break_buf == break_pattern:
            logger.debug('Found a serial break.')
            return True
    return False

while True:
    # Transmit data from the serial port to the USB port.
    sercomm_waiting = sercomm.inWaiting()
    if sercomm_waiting > 0:
        xscomm_free = xscomm.get_send_buffer_space()
        n = min(sercomm_waiting, xscomm_free)
        if n>0:
            logger.debug('sercomm_waiting = %d, xscomm_free = %d' % (sercomm_waiting, xscomm_free))
            buf = sercomm.read(n)
            buf = [ord(c) for c in buf]
            logger.debug('%s: %s' % (sercomm.name, ' '.join(['%02x' % b for b in buf])))
            xscomm.send(buf)
            if break_found(buf):
                xsreset.write(1)
                logger.debug('Reset sent.')
        
    # Transmit data from the USB port to the serial port.
    xscomm_waiting = xscomm.get_recv_buffer_length()
    if xscomm_waiting > 0:
        logger.debug('xscomm_waiting = %d' % xscomm_waiting)
        #buf = [chr(d.unsigned) for d in xscomm.receive(num_words=xscomm_waiting, always_list=True)]
        buf = [chr(d.unsigned) for d in xscomm.receive(always_list=True)]
        logger.debug('USB%d,%02x: %s' % (args.usb, args.module, ' '.join(['%02x' % ord(b) for b in buf])))
        sercomm.write(buf)

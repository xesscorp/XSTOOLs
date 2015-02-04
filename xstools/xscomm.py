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
Class for managing communication streams to/from the FPGA.
"""

from xsmemio import *


class XsCommException(Exception):
    pass


class XsComm:

    """
    This class instantiates an object that will communicate bidirectionally
    through the JTAG port of the FPGA to a module within the FPGA.
    """

    # Constants for the communication interface.
    _FIFO_ADDR = 0  # Address for sending/receiving data to/from the FPGA.
    _STATUS_ADDR = 1  # Address for getting status on the send/recv comm channels.
    _CONTROL_ADDR = 1  # Write to this address to reset the entire comm channel.
    _DN_FREE_ADDR = 2  # Read this address to get the # of words of free space in the download FIFO.
    _UP_USED_ADDR = 3  # Read this address to get the # of words waiting in the upload FIFO.
    _BREAK_ADDR = 4  # Write to this address to send a break command.
    def __init__(
        self,
        xsusb_id=DEFAULT_XSUSB_ID,
        module_id=DEFAULT_MODULE_ID,
        xsjtag=None
    ):
        """Setup a communication object.

        xsusb_id = The ID for the USB port.
        module_id = The ID for the DUT I/O module in the FPGA.
        xsjtag = The Xsjtag USB port object. (Use this if not using xsusb_id.)
        """

        # Setup the interface to the communication module registers.
        self._memio = XsMemIo(xsusb_id=xsusb_id, module_id=module_id, xsjtag=xsjtag)
        logging.debug('address width = '
                      + str(self._memio.address_width))
        logging.debug('data width = ' + str(self._memio.data_width))

    def reset(self):
        """Reset the communication channel hardware in the FPGA."""
        self._memio.write(self._CONTROL_ADDR, [0])

    def get_send_buffer_space(self):
        """Return the amount of space available in the FPGA to receive data."""
        return reduce(lambda s,d: s*256+d.unsigned, reversed(self._memio.read(self._DN_FREE_ADDR, 4)), 0)

    def get_recv_buffer_length(self):
        """Return the amount of data waiting in the FPGA to be transmitted."""
        return reduce(lambda s,d: s*256+d.unsigned, reversed(self._memio.read(self._UP_USED_ADDR, 4)), 0)

    def get_levels(self):
        """Get the amount of space available in the FPGA to receive data and the amount of data
        waiting in the FPGA to be transmitted."""
        print "available = %d  waiting = %d" % (self.get_send_buffer_space(), self.get_recv_buffer_length())
        
    def send_break(self):
        """Send a break command."""
        self._memio.write(self._BREAK_ADDR, [0])

    def send(self, buffer, wait=True):
        """Send buffer contents through the comm channel to the FPGA.

        Keyword arguments:
        buffer -- List of words or a single integer to send to the FPGA.
        wait -- If true, wait until space is available in the FPGA to accept the buffer (default True).
        """

        if isinstance(buffer, int):
            buffer = [buffer]
        if len(buffer) == 0:
            return

        space_avail = self.get_send_buffer_space()

        if space_avail < len(buffer) and not wait:
            raise XsCommException('Not enough room to send transmit buffer.')

        num_words_sent = 0
        while num_words_sent < len(buffer):
            if space_avail is not 0:
                self._memio.write(self._FIFO_ADDR, buffer[num_words_sent: num_words_sent + space_avail])
                num_words_sent += space_avail
            space_avail = self.get_send_buffer_space()

    def receive(self, num_words=None, wait=True, drain=True, always_list=False):
        """Return a buffer of data received from the FPGA through the comm channel.

        Keyword arguments:
        num_words -- The number of words to get from the FPGA (default None).
        wait -- If true, wait until the number of words requested is available (default True).
        drain -- If true and num_words==None, then take everything currently stored in the FPGA transmit buffer (default True).
        always_list -- If true, always return a list even if there is only one word in it.
        """

        num_words_avail = self.get_recv_buffer_length()

        if drain and num_words is None:
            buffer = self._memio.read(self._FIFO_ADDR, num_words_avail)

        elif num_words_avail < num_words and not wait:
            raise XsCommException('Too little data to fill receive buffer.')

        else:
            buffer = []
            num_words_needed = num_words
            while num_words_needed > 0:
                if num_words_avail is not 0:
                    buffer.extend(self._memio.read(self._FIFO_ADDR, min(num_words_needed, num_words_avail)))
                    num_words_needed = num_words - len(buffer)
                num_words_avail = self.get_recv_buffer_length()
        
        if always_list and type(buffer) != list:
            buffer = [buffer]
        return buffer

if __name__ == '__main__':
    # logging.root.setLevel(logging.DEBUG)

    print '\n', '='*70, "\nThe FPGA should be freshly loaded before running this test script!\n", '='*70, '\n'

    USB_ID = 0  # This is the USB index for the XuLA board connected to the host PC.
    comm = XsComm(xsusb_id=USB_ID)
    print comm._memio._get_mem_widths()
    
    comm.get_levels()
    recv = comm.receive(14)
    print "Receive = ", [d.unsigned for d in recv]
    comm.get_levels()
    recv = comm.receive(drain=True)
    print "Receive = ", [d.unsigned for d in recv]
    comm.get_levels()
    comm.send([15, 16, 17, 18, 19, 20, 21, 22, 23, 24])
    comm.send([15, 16, 17, 18, 19, 20, 21, 22, 23, 24])
    comm.get_levels()
    recv = comm.receive(10)
    print "Receive = ", [d.unsigned for d in recv]
    comm.get_levels()
    recv = comm.receive(10)
    print "Receive = ", [d.unsigned for d in recv]
    comm.get_levels()

    print "\n\nRESET\n\n"
    comm.reset()

    comm.get_levels()
    comm.send([1, 2, 3, 4, 5, 6, 7, 8])
    comm.get_levels()
    comm.send([9, 10, 11, 12, 13, 14, 15, 16])
    comm.get_levels()
    recv = comm.receive(16)
    print "Receive = ", [d.unsigned for d in recv]
    comm.get_levels()
    comm.send([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    comm.get_levels()
    recv = comm.receive()
    comm.get_levels()
    print "Receive = ", [d.unsigned for d in recv]
    comm.get_levels()

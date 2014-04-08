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
    _FIFO_ADDR = 0 # Address for sending/receiving data to/from the FPGA.
    _STATUS_ADDR = 1 # Address for getting status on the send/recv comm channels.
    _CONTROL_ADDR = 1 # Write to this address to reset the entire comm channel.
    _DN_FREE_ADDR = 2 # Read this address to get the amount of free space in the download FIFO.
    _UP_USED_ADDR = 3 # Read this address to get the # of words waiting in the upload FIFO.

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
        """Reset the communication hardware in the FPGA."""
        self._memio.write(self._CONTROL_ADDR, [0])
        
    def get_send_buffer_space(self):
        """Return the amount of space available in the FPGA to receive data."""
        return self._memio.read(self._DN_FREE_ADDR, 1).unsigned
        
    def get_recv_buffer_length(self):
        """Return the amount of data waiting in the FPGA to be transmitted."""
        return self._memio.read(self._UP_USED_ADDR, 1).unsigned
        
    def get_levels(self):
        """Get the amount of space available to receive data and the amount of data
        waiting to be transmitted."""
        print "available = %d  waiting = %d" % (self.get_send_buffer_space(), self.get_recv_buffer_length())

    def send(self, packet):
        """Send a packet of data through the comm channel to the FPGA."""

        if isinstance(packet, int):
            packet = [packet]
        if len(packet) == 0:
            return

        if self.get_send_buffer_space() >= len(packet):
            self._memio.write(self._FIFO_ADDR, packet)
        else:
            raise XsCommException('Not enough room to send data packet.')
            
    def receive(self, num_data=0):
        """Receive a packet of data from the FPGA through the comm channel."""
        
        if num_data == 0:
            return []
        
        if self.get_recv_buffer_length() >= num_data:
            return self._memio.read(self._FIFO_ADDR, num_data)
        else:
            raise XsCommException('Too little data to fill data packet.')

if __name__ == '__main__':
    #logging.root.setLevel(logging.DEBUG)
    
    USB_ID = 0  # This is the USB index for the XuLA board connected to the host PC.
    comm = XsComm(xsusb_id=USB_ID)
    print comm._memio._get_mem_widths()
    
    comm.get_levels()
    recv = comm.receive(14)
    print "Receive = ", [d.unsigned for d in recv]
    comm.get_levels()
    recv = comm.receive(7)
    print "Receive = ", [d.unsigned for d in recv]
    comm.get_levels()
    comm.send([15,16,17,18,19,20,21,22,23,24])
    comm.send([15,16,17,18,19,20,21,22,23,24])
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
    comm.send([1,2,3,4,5,6,7,8])
    comm.get_levels()
    comm.send([9,10,11,12,13,14,15,16])
    comm.get_levels()
    recv = comm.receive(16)
    print "Receive = ", [d.unsigned for d in recv]
    comm.get_levels()
    comm.send([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])
    comm.get_levels()
    recv1 = comm.receive(8)
    comm.get_levels()
    recv2 = comm.receive(8)
    print "Receive = ", [d.unsigned for d in recv1+recv2]
    comm.get_levels()
    
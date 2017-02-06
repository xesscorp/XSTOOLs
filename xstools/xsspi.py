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
Class for interfacing to SPI devices.
"""
import logging

from xstools.xshostio import DEFAULT_XSUSB_ID, DEFAULT_MODULE_ID
from xstools.xsmemio import XsMemIo


class XsSpi:
    """
    This class instantiates an object that will communicate through the JTAG
    port of the FPGA to an SPI master core that can communicate with SPI slaves
    external to the FPGA.
    """

    # Constants for the SPI interface.
    _RESET_ADDR = 0  # Reset SPI interface.
    # Single SPI transfer and then SPI device is de-selected.
    _SINGLE_XFER_ADDR = 1
    # Multiple transfers and then SPI device is left selected for further xfers.
    _MULTI_XFER_ADDR = 2

    def __init__(
        self,
        xsusb_id=DEFAULT_XSUSB_ID,
        module_id=DEFAULT_MODULE_ID,
        xsjtag=None
        ):
        """Setup an I2C I/O object.
        
        xsusb_id = The ID for the USB port.
        module_id = The ID for the DUT I/O module in the FPGA.
        xsjtag = The Xsjtag USB port object. (Use this if not using xsusb_id.)
        """

        # Setup the interface to the SPI module registers.
        self._memio = XsMemIo(xsusb_id=xsusb_id, module_id=module_id,
                              xsjtag=xsjtag)
        logging.debug('address width = '
                      + str(self._memio.address_width))
        logging.debug('data width = ' + str(self._memio.data_width))
        
    def reset(self):
        self._memio.write(self._RESET_ADDR, [0])

    def send(self, packet, stop=True):
        """Send a packet of data to the SPI device.
        
        packet = The list of data to send to the device.
        stop = True if the chip-select should be raised after sending.
        """

        if isinstance(packet, int):
            packet = [packet]
        if len(packet) == 0:
            if stop:
                # Reset the SPI interface to de-select the SPI device.
                self.reset()
            return

        if not stop:
            self._memio.write(self._MULTI_XFER_ADDR, packet)
        else:
            self.send(packet[:-1], stop=False)
            self._memio.write(self._SINGLE_XFER_ADDR, packet[-1:])
            
    def receive(self, num_data=0, stop=True):
        """Receive a packet of data from the SPI slave."""
        
        if num_data == 0:
            if stop:
                # Reset the SPI interface to de-select the SPI device.
                self.reset()
            return []
            
        if not stop:
            return self._memio.read(self._MULTI_XFER_ADDR, num_data)
        else:
            packet = self.receive(num_data-1, stop=False)
            packet.append(self._memio.read(self._SINGLE_XFER_ADDR))
            return packet

if __name__ == '__main__':
    # logging.root.setLevel(logging.DEBUG)

    # This is the USB index for the XuLA board connected to the host PC.
    USB_ID = 0
    SPI_ID = 0xf0
    spi = XsSpi(xsusb_id=USB_ID, module_id=SPI_ID)
    print(spi._memio._get_mem_widths())
    import sys
    # sys.exit(0)
    
    spi.reset()
    print(spi._memio._get_mem_widths())
    spi.send([1,2,3,4], stop=True)
    print(spi._memio._get_mem_widths())
    spi.send([1], stop=True)
    print(spi._memio._get_mem_widths())
    spi.send([1,2,3,4,5], stop=False)
    print(spi._memio._get_mem_widths())
    spi.send([1], stop=False)
    print(spi._memio._get_mem_widths())
    spi.reset()
    print(spi._memio._get_mem_widths())
    
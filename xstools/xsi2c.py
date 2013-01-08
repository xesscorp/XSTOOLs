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
Class for interfacing to I2C devices using the I2C FPGA core
found at http://opencores.org/project,i2c.
"""

from xsmemio import *

# Constants for the I2C interface.

_ACK = 0  # I2C acknowledge level.
_NACK = 1  # I2C no-acknowledge level.

_READ_OP = 1  # I2C read operation.
_WRITE_OP = 0  # I2C write operation.

# I2C module register addresses from page 4 of http://opencores.org/svnget,i2c?file=%2Ftrunk%2F%2Fdoc%2Fi2c_specs.pdf

_PRERlo = 0x00  # Lower byte of clock prescale register.
_PRERhi = 0x01  # Upper byte of clock prescaler register.
_CTR = 0x02  # Control register.
_TXR = 0x03  # Transmit register.
_RXR = 0x03  # Receive register.
_CR = 0x04  # Command register.
_SR = 0x04  # Status register.

_CTR_EN = 7  # When true, enable the I2C module.
_CTR_IEN = 6  # When true, enable the I2C module interrupt.

_CR_STA = 7  # When true, generate start condition.
_CR_STO = 6  # When true, generate stop condition.
_CR_RD = 5  # When true, read from slave.
_CR_WR = 4  # When true, write to slave.
_CR_ACK = 3  # When acting as a receiver, clear to send ACK(0) or set to send NACK(1).
_CR_IACK = 0  # When set, clear a pending interrupt.

_SR_RXACK = 7  # Indicates the ACK(0) or NACK(1) from the slave.
_SR_BUSY = 6  # True after start detected, false after stop detected.
_SR_AL = 5  # True when bus arbitration has been lost.
_SR_TIP = 1  # True when transfer is in progress.
_SR_IF = 0  # True when an interrupt is pending.


class XsI2c:
    """
    This class instantiates an object that will communicate through the JTAG
    port of the FPGA to an I2C master core found at http://opencores.org/project,i2c.
    The I2C master can communicate with I2C slaves external to the FPGA.
    """

    def __init__(
        self,
        xsusb_id=DEFAULT_XSUSB_ID,
        module_id=DEFAULT_MODULE_ID,
        xsjtag=None,
        i2c_address=0,
        ):
        """Setup an I2C I/O object.
        
        xsusb_id = The ID for the USB port.
        module_id = The ID for the DUT I/O module in the FPGA.
        xsjtag = The Xsjtag USB port object. (Use this if not using xsusb_id.)
        i2c_address = The I2C address for the chip we're talking to.
        """

        # Setup the interface to the I2C module registers.
        self._memio = XsMemIo(xsusb_id, module_id, xsjtag)
        logging.debug('address width = '
                      + str(self._memio.address_width))
        logging.debug('data width = ' + str(self._memio.data_width))

        self._i2c_address = i2c_address
        self._enable()
        
    def _enable(self):
        """Enable the I2C interface."""
        self._memio.write(_CTR, [1 << _CTR_EN])
        
    def _disable(self):
        """Disable the I2C interface."""
        self._memio.write(_CTR, [0])

    def _check_for_ack(self):
        """Check for acknowledgement signal from the I2C slave."""

        # Wait while the transfer is in-progress on the I2C bus.
        sr = self._memio.read(_SR)
        while sr[_SR_TIP] == 1:
            sr = self._memio.read(_SR)

        # Bus transaction complete, so see if it was acknowledged.
        if sr[_SR_RXACK] == _NACK:
            raise XsMinorError('%x: I2C NACK' % self._i2c_address)

    def _send_i2c_address(self, op):
        """Transmit I2C slave address along with R/W operation bit."""

        # The address is created by shifting the I2C address and setting the LSB with the read/write opcode.
        address = self._i2c_address << 1 & 0xfe | op

        # Write the address into the transmit register.
        self._memio.write(_TXR, [address])

        # Set the START condition for an I2C transfer and initiate the transmission of the I2C address.
        self._memio.write(_CR, [1 << _CR_STA | 1 << _CR_WR])
        self._check_for_ack()

    def _send_byte(self, byte, stop=1):
        """Send a byte to the I2C slave."""

        # Load the transmitter register.
        self._memio.write(_TXR, [byte])

        # Initiate the transmission and set the stop bit as directed.
        self._memio.write(_CR, [1 << _CR_WR | stop << _CR_STO])
        self._check_for_ack()

    def _send_bytes(self, bytes, stop=1):
        """Send multiple bytes to the I2C slave."""

        # Send the first N-1 bytes in the N-byte data set.
        for b in bytes[:-1]:
            self._send_byte(b, stop=0)

        # Send the last byte in the data set and then stop the transmission.
        b = bytes[-1]
        self._send_byte(b, stop=stop)

    def send(self, packet, stop=1):
        """Send the slave's I2C address and then a packet of data."""

        self._send_i2c_address(_WRITE_OP)
        self._send_bytes(bytes=packet, stop=stop)

    def wr_reg(self, reg_address, value):
        """Write a register in the I2C slave with a value."""

        packet = [reg_address]
        packet.extend(value)
        self.send(packet=packet, stop=1)

    def _rcv_byte(self, stop=1, ack=_ACK):
        """Receive a byte from the I2C slave."""

        # Receive the byte with the stop and acknowledge bits set as directed.
        self._memio.write(_CR, [1 << _CR_RD | ack << _CR_ACK | stop
                          << _CR_STO])

        # Wait while byte transfer is in-progress.
        while self._memio.read(_SR)[_SR_TIP] == 1:
            pass

        # Return byte read from slave.
        return self._memio.read(_RXR).unsigned

    def _rcv_bytes(self, num_bytes=0):
        """Receive multiple bytes from the I2C slave."""

        bytes = []
        if num_bytes>0:

            # Receive the first N-1 bytes from the slave.
            for i in range(0, num_bytes - 1):
                bytes.append(self._rcv_byte(stop=0, ack=_ACK))

            # Receive the last byte which gets NACK'ed and the reception stops.
            bytes.append(self._rcv_byte(stop=1, ack=_NACK))

        return bytes

    def receive(self, num_bytes=0):
        """Receive a packet of N bytes from the I2C slave."""

        # Send the address of the slave onto the I2C bus.
        self._send_i2c_address(_READ_OP)
        
        # Get the data output by the slave and return it.
        return self._rcv_bytes(num_bytes)

    def rd_reg(self, reg_address, num_bytes=1):
        """Read the value from a register in the I2C slave."""

        # Transmit register address to the I2C slave, but don't release the bus.
        self.send([reg_address], stop=0)
        
        # Now get the value in the register and return it.
        return self.receive(num_bytes)


if __name__ == '__main__':
    import sys
    import random
    from bitarray import *
    from scipy import *
    from pylab import *

    USB_ID = 0  # This is the USB index for the XuLA board connected to the host PC.
    I2C_ID = 0xff
    i2c = XsI2c(xsusb_id=USB_ID, module_id=I2C_ID, i2c_address=0x58)
    
    i2c.wr_reg(0x02, [0x01, 0x80])
    i2c.wr_reg(0x08, [0x80, 0x00])
    i2c.wr_reg(0x0e, [0xf0])
    sys.exit(0)
    
    print i2c.rd_reg(0x0e)
    i2c.wr_reg(0x0e, [7])
    print i2c.rd_reg(0x0e)
    i2c.wr_reg(0x0e, [0])
    print i2c.rd_reg(0x0e)
    i2c.wr_reg(0x02,[0x12, 0xc0])
    print i2c.rd_reg(0x02,2)
    print i2c.rd_reg(0x0d,1)
    

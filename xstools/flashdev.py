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
#   (c)2013 - X Engineering Software Systems Corp. (www.xess.com)
# **********************************************************************

"""
Classes for devices containing flash memory.
"""

import logging
from intelhex import IntelHex
from xserror import *
from xsspi import *
from xilbitstr import *      


class FlashDevice:

    """Generic flash memory object."""

    def __init__(self):
        """Initialize the serial flash."""
        pass
        
    def _floor_blk_addr(self, addr, blk_sz):
        return addr & ((1<<32) - blk_sz)
        
    def _ceil_blk_addr(self, addr, blk_sz):
        return ((addr + blk_sz - 1) // blk_sz) * blk_sz
        
    def _set_blk_bounds(self, bottom, top, blk_sz):
        bottom = self._START_ADDR if (bottom == None or bottom < self._START_ADDR) else self._floor_blk_addr(bottom, blk_sz)
        top = self._END_ADDR if (top == None or top >= self._END_ADDR) else self._ceil_blk_addr(top, blk_sz)
        if bottom > top:
            raise XsMinorError('Bottom address is greater than the top address.')
        return (bottom, top)

    def erase(self, bottom=None, top=None):
        """Erase a section of the flash."""

        (bottom, top) = self._set_blk_bounds(bottom, top, self._ERASE_BLK_SZ)
        for addr in range(bottom, top, self._ERASE_BLK_SZ):
            self.erase_blk(addr)

    def write(self, hexfile, bottom=None, top=None):
        """Download a hexfile into a section of the flash.
        THE FLASH MUST ALREADY BE ERASED FOR THIS TO WORK CORRECTLY!
        """

        # If the argument is not already a hex data object, then it must be a file name, so read the hex data from it.
        if not isinstance(hexfile, IntelHex):
            try:
                hexfile_data = IntelHex(hexfile)
                hexfile = hexfile_data
            except:
                # OK, didn't read as an Intel hex file, so try reading it as a Xilinx bitstream file.
                try:
                    bitstream_data = XilinxBitstream(hexfile)
                    hexfile = bitstream_data.to_intel_hex()
                except:
                    # Error: neither an Intel hex or Xilinx bitstream file.
                    raise XsMajorError('Unable to convert file %s for writing to %s flash.'
                                    % (hexfile, self.device_name))
            if bottom == None:
                bottom = hexfile.minaddr()
            if top == None:
                top = hexfile.maxaddr()
            # hex data must be empty if min and/or max address is undefined.
            if bottom == None or top == None:
                bottom, top = (0,0)

        (bottom, top) = self._set_blk_bounds(bottom, top, self._WRITE_BLK_SZ)
        for addr in range(bottom, top, self._WRITE_BLK_SZ):
            # The tobinarray() method fills unused array locations with 0xFF so the flash at those
            # addresses will stay unprogrammed.
            data_blk = bytearray(hexfile.tobinarray(start=addr, size=self._WRITE_BLK_SZ))
            # Don't write data blocks that only contain the value 0xFF (erased value of flash).
            if data_blk.count(chr(0xff)) != self._WRITE_BLK_SZ:
                self.write_blk(addr, data_blk)

    def read(self, bottom=None, top=None):
        """Return the hex data stored in a section of the flash."""

        (bottom, top) = self._set_blk_bounds(bottom, top, self._WRITE_BLK_SZ)
        data = bytearray()
        for addr in range(bottom, top, self._READ_BLK_SZ):
            data.extend(self.read_blk(addr, self._READ_BLK_SZ))
        hex_data = IntelHex()
        hex_data[bottom:top] = [byte for byte in data]
        return hex_data

    def verify(self, hexfile, bottom=None, top=None):
        """Verify the program in the flash matches the hex file."""

        # If the argument is not already a hex data object, then it must be a file name, so read the hex data from it.
        if not isinstance(hexfile, IntelHex):
            try:
                hexfile_data = IntelHex(hexfile)
                hexfile = hexfile_data
            except:
                raise XsMajorError('Unable to open hex file %s for verifying %s flash.'
                                    % (hexfile, self.device_name))

        (bottom, top) = self._set_blk_bounds(bottom, top, self._WRITE_BLK_SZ)
        flash = self.read(bottom, top)
        errors = [(a, flash[a], hexfile[a]) for a in
                  sorted(hexfile.todict().keys()) if flash[a]
                  != hexfile[a] and bottom <= a < top]
        if len(errors) > 0:
            raise XsMajorError('%s flash != hex file at %d locations starting at address 0x%04x (0x%02x != 0x%02x)'
                                % (self.device_name, len(errors), errors[0][0], errors[0][1], errors[0][2]))

    def program(self, hexfile, bottom=None, top=None):
        """Erase, write and verify the flash with the contents of the hex file."""

        self.erase(bottom, top)
        self.write(hexfile, bottom, top)
        self.verify(hexfile, bottom, top)

        
_MODULE_ID = 0xf0  # Default module ID for JTAG interface to serial configuration flash.
        
class W25X(FlashDevice):
    """Winbond serial flash memory."""
    
    device_name_prefix = 'W25X'
    mfg_id = 0xef
    chip_info = {
        0x3011:{'size':2**20, 'name':'10'},
        0x3012:{'size':2**21, 'name':'20'}, 
        0x3013:{'size':2**22, 'name':'40'}, 
        0x3014:{'size':2**23, 'name':'80'},
        0x4014:{'size':2**23, 'name':'80'}, # This is actually for a W25Q80 serial flash.
        }

    _START_ADDR = 0x00000
    _WRITE_BLK_SZ = 256
    _READ_BLK_SZ = 256
    _WORD_SZ = 8
    _BUSY_BIT = 0
    
    _JEDEC_ID_CMD = 0x9f
    _READ_STATUS_CMD = 0x05
    _WRITE_ENABLE_CMD = 0x06
    _CHIP_ERASE_CMD = 0xc7
    _PAGE_PROGRAM_CMD = 0x02
    _FAST_READ_CMD = 0x0b
    

    def __init__(
        self,
        xsusb_id=DEFAULT_XSUSB_ID,
        module_id=DEFAULT_MODULE_ID,
        xsjtag=None
        ):
        self._spi = XsSpi(xsjtag=xsjtag, module_id=module_id)
        mfg_id, jedec_id = self.get_chip_id()
        if mfg_id != self.mfg_id:
            raise XsMajorError('Incorrect manufacturer identifier for the W25X serial flash.')
        self.chip_size = self.get_chip_size(jedec_id)
        self._END_ADDR = self.chip_size // 8
        self._ERASE_BLK_SZ = self._END_ADDR
        self.device_name = self.device_name_prefix + self.chip_info[jedec_id]['name']

    def get_chip_id(self):
        self._spi.send(self._JEDEC_ID_CMD, stop=False)
        (mfg_id, jedec_id_hi, jedec_id_lo) = self._spi.receive(num_data=3, stop=True)
        return (mfg_id.uint, (jedec_id_lo + jedec_id_hi).uint)
        
    def get_chip_size(self, jedec_id):
        if jedec_id not in self.chip_info :
            raise XsMajorError('Incorrect JEDEC identifier for the W25X serial flash.')
        return self.chip_info[jedec_id]['size']
        
    def _is_busy(self):
        status = self._spi.receive(num_data=1, stop=False).uint
        return status & (1<<self._BUSY_BIT) != 0
        
    def _addr_bytes(self, addr):
        return [addr >> 16 & 0xff, addr >> 8 & 0xff, addr & 0xff]

    def erase_blk(self, addr):
        self._spi.send(self._WRITE_ENABLE_CMD, stop=True)
        self._spi.send(self._CHIP_ERASE_CMD, stop=True)
        self._spi.send(self._READ_STATUS_CMD, stop=False)
        while(self._is_busy()):
            pass
        self._spi.reset()
        
    def write_blk(self, addr, data):
        self._spi.send(self._WRITE_ENABLE_CMD, stop=True)
        self._spi.send(self._PAGE_PROGRAM_CMD, stop=False)
        self._spi.send(self._addr_bytes(addr), stop=False)
        self._spi.send(data, stop=True)
        self._spi.send(self._READ_STATUS_CMD, stop=False)
        while(self._is_busy()):
            pass
        self._spi.reset()

    def read(self, bottom=None, top=None):
        """Return the hex data stored in a section of the flash."""

        if bottom > top:
            raise XsMinorError('Bottom address is greater than the top address.')
        self._spi.send(self._FAST_READ_CMD, stop=False)
        self._spi.send(self._addr_bytes(bottom), stop=False)
        self._spi.send([0], stop=False)
        data = self._spi.receive(num_data=top-bottom, stop=True)
        hex_data = IntelHex()
        hex_data[bottom:top] = [byte.uint for byte in data]
        return hex_data
        
if __name__ == '__main__':
    #logging.root.setLevel(logging.DEBUG)
    
    USB_ID = 0  # This is the USB index for the XuLA board connected to the host PC.
    SPI_ID = 0xf0
    flash = W25X(xsusb_id=USB_ID, module_id=SPI_ID)
    mfg_id, jedec_id = flash.get_chip_id()
    print '%x %x' % (mfg_id, jedec_id)
    print '%x' % flash.get_chip_size(jedec_id)
    print flash.device_name
    print '%x' % flash._END_ADDR
    #import sys
    #sys.exit(0)

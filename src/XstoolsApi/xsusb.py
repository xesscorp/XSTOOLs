# /***********************************************************************************
# *   This program is free software; you can redistribute it and/or
# *   modify it under the terms of the GNU General Public License
# *   as published by the Free Software Foundation; either version 2
# *   of the License, or (at your option) any later version.
# *
# *   This program is distributed in the hope that it will be useful,
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# *   GNU General Public License for more details.
# *
# *   You should have received a copy of the GNU General Public License
# *   along with this program; if not, write to the Free Software
# *   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# *   02111-1307, USA.
# *
# *   (c)2012 - X Engineering Software Systems Corp. (www.xess.com)
# ***********************************************************************************/

'''
XESS USB interface.
'''

import usb.core
import usb.util
    
class XsUsb:
    _VENDOR_ID = 0x04d8
    _PRODUCT_ID = 0xff8c
    _DEFAULT_ENDPOINT = 0x01
    _TIMEOUT = 100  # USB read/write transfer timeout in milliseconds.

    #  XESS USB commands.
    READ_VERSION_CMD       = 0x00
    READ_FLASH_CMD         = 0x01
    WRITE_FLASH_CMD        = 0x02
    ERASE_FLASH_CMD        = 0x03
    READ_EEDATA_CMD        = 0x04
    WRITE_EEDATA_CMD       = 0x05
    READ_CONFIG_CMD        = 0x06
    WRITE_CONFIG_CMD       = 0x07
    ID_BOARD_CMD           = 0x31
    UPDATE_LED_CMD         = 0x32
    INFO_CMD               = 0x40
    SENSE_INVERTERS_CMD    = 0x41
    TMS_TDI_CMD            = 0x42
    TMS_TDI_TDO_CMD        = 0x43
    TDI_TDO_CMD            = 0x44
    TDO_CMD                = 0x45
    TDI_CMD                = 0x46
    RUNTEST_CMD            = 0x47
    NULL_TDI_CMD           = 0x48
    PROG_CMD               = 0x49
    SINGLE_TEST_VECTOR_CMD = 0x4a
    GET_TEST_VECTOR_CMD    = 0x4b
    SET_OSC_FREQ_CMD       = 0x4c
    ENABLE_RETURN_CMD      = 0x4d
    DISABLE_RETURN_CMD     = 0x4e
    JTAG_CMD               = 0x4f
    FLASH_ONOFF_CMD        = 0x50
    RESET_CMD              = 0xff    

    # XESS USB JTAG_CMD flag fields.
    GET_TDO_MASK = 0x01
    PUT_TMS_MASK = 0x02
    TMS_VAL_MASK = 0x04
    PUT_TDI_MASK = 0x08
    TDI_VAL_MASK = 0x10

    @classmethod
    def get_num_xsusb(cls):
        return len(usb.core.find(idVendor=cls._VENDOR_ID, idProduct=cls._PRODUCT_ID, find_all=True))
    
    def __init__(self, xsusb_id=0, endpoint=1):
        devs = usb.core.find(idVendor=self._VENDOR_ID, idProduct=self._PRODUCT_ID, find_all=True)
        if devs == []:
            raise ValueError('XESS USB device not found')
        self._dev = devs[xsusb_id]
        self._endpoint = endpoint;
    
    def write(self, data):
        print 'OUT => ', [bin((x)|0x100)[3:] for x in data]
        self._dev.write(usb.util.ENDPOINT_OUT | self._endpoint, data, 0, self._TIMEOUT)
        return
    
    def read(self, num_bytes=0):
        data = self._dev.read(usb.util.ENDPOINT_IN | self._endpoint, num_bytes, 0, self._TIMEOUT)
        print 'IN <=  ', [bin(x|0x100)[3:] for x in data]
        return data
#        return self._dev.read(usb.util.ENDPOINT_IN | self._endpoint, num_bytes, 0, self._TIMEOUT)


if __name__ == '__main__':
    print '#XSUSB = %d' % XsUsb.get_num_xsusb()
    xsusb = XsUsb()
    xsusb.write([1,2,3,4])
    print xsusb.read(4)

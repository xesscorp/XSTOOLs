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

"""
Xilinx FPGA object.
"""

import logging
import time
from xsjtag import *
from xilbitstr import *

class XilinxFpga():
    """Generic Xilinx FPGA object."""
    
    def __init__(self, xsjtag_port=None):
        self.xsjtag_port = xsjtag_port
        
    def configure(self, bitstream=None):
        if type(bitstream) is str:
            bitstream = XilinxBitstream(bitstream)
        if bitstream.device_type != self._DEVICE_TYPE:
            print "ERROR: mismatched device types: %s != %s" % (bitstream.device_type, self._DEVICE_TYPE)
            return False
        # xapp139 - 
        # http://www.xilinx.com/support/documentation/application_notes/xapp452.pdf
        # Must follow JPROGRAM with CFG_IN to keep device locked to JTAG.
        # See AR 16829.
        self.xsjtag_port.load_ir_then_dr(instruction=self._JPROGRAM_INSTR)
        self.xsjtag_port.load_ir_then_dr(instruction=self._CFG_IN_INSTR)
        time.sleep(0.001)
        self.xsjtag_port.load_ir_then_dr(instruction=self._CFG_IN_INSTR, data=bitstream.bits)
        # BEFORE: (wants CCLK as startup clock)
        #self.tlr()
        #self.LoadBSIRthenBSDR(self.JSTART, None)
        # NOW: (works OK with JTAG Clock as startup clock)
        self.xsjtag_port.load_ir_then_dr(instruction=self._JSTART_INSTR)
        self.xsjtag_port.runtest(num_tcks=12)
        self.xsjtag_port.load_ir_then_dr(instruction=self._JSTART_INSTR, data=XsBitarray(22))
        self.xsjtag_port.reset_tap()
        return True
        
    def get_idcode(self):
        # Enter the IDCODE instruction into the JTAG IR and then return the 32 ID bits.
        return self.xsjtag_port.load_ir_then_dr(instruction=self._IDCODE_INSTR, data=None, num_return_bits=32)
        
    def get_status(self):
        # This is the command for reading the status register from UG332, pg 340.
        command = XsBitarray('1010101010011001') # 0xaa99
        command.extend(XsBitarray('0010000000000000')) # 0x2000
        command.extend(XsBitarray('0010100100000001')) # 0x2901
        command.extend(XsBitarray('0010000000000000')) # 0x2000
        command.extend(XsBitarray('0010000000000000')) # 0x2000
        self.xsjtag_port.load_ir_then_dr(instruction=self._CFG_IN_INSTR, data=command)
        # Now read the 32 bits from the status register.
        status_bits = self.xsjtag_port.load_ir_then_dr(instruction=self._CFG_OUT_INSTR, num_return_bits=32)
        status = {
            'SYNC_TIMEOUT' :   status_bits[15],
            'SEU_ERR':         status_bits[14],
            'DONE':            status_bits[13],
            'INIT':            status_bits[12],
            'MODE':            status_bits[9:12],
            'VSEL':            status_bits[6:9],
            'GHIGH_B':         status_bits[5],
            'GWE':             status_bits[4],
            'GTS_CFG_B':       status_bits[3],
            'DCM_LOCK':        status_bits[2],
            'ID_ERROR':        status_bits[1],
            'CRC_ERROR':       status_bits[0]
        }
        return status

class Xc3sa(XilinxFpga):
    """Generic Xilinx Spartan-3A FPGA object."""

    # Spartan-3A JTAG instruction opcodes.
    _SAMPLE_INSTR      = XsBitarray('000001'[::-1])
    _USER1_INSTR       = XsBitarray('000010'[::-1])
    _USER2_INSTR       = XsBitarray('000011'[::-1])
    _CFG_OUT_INSTR     = XsBitarray('000100'[::-1])
    _CFG_IN_INSTR      = XsBitarray('000101'[::-1])
    _INTEST_INSTR      = XsBitarray('000111'[::-1])
    _USERCODE_INSTR    = XsBitarray('001000'[::-1])
    _IDCODE_INSTR      = XsBitarray('001001'[::-1])
    _HIGHZ_INSTR       = XsBitarray('001010'[::-1])
    _JPROGRAM_INSTR    = XsBitarray('001011'[::-1])
    _JSTART_INSTR      = XsBitarray('001100'[::-1])
    _JSHUTDOWN_INSTR   = XsBitarray('001101'[::-1])
    _EXTEST_INSTR      = XsBitarray('001111'[::-1])
    _ISC_ENABLE_INSTR  = XsBitarray('010000'[::-1])
    _ISC_PROGRAM_INSTR = XsBitarray('010001'[::-1])
    _ISC_NOOP_INSTR    = XsBitarray('010100'[::-1])
    _ISC_READ_INSTR    = XsBitarray('010101'[::-1])
    _ISC_DISABLE_INSTR = XsBitarray('010110'[::-1])
    _ISC_DNA_INSTR     = XsBitarray('110001'[::-1])
    _BYPASS_INSTR      = XsBitarray('111111'[::-1])
    
    def __init__(self, xsjtag_port=None):
        XilinxFpga.__init__(self,xsjtag_port=xsjtag_port)
        
class Xc3s200avq100(Xc3sa):
    """200 Kgate Spartan-3A FPGA in VQ100 package."""
    
    _DEVICE_TYPE = '3s200avq100'
    _IDCODE      = XsBitarray('00000010001000011000000010010011'[::-1])

    def __init__(self, xsjtag_port=None):
        Xc3sa.__init__(self,xsjtag_port=xsjtag_port)


if __name__ == "__main__":

    #logging.root.setLevel(logging.DEBUG)
    xsusb = XsUsb()
    xc3s200a = Xc3s200avq100(XsJtag(xsusb))
    print xc3s200a.get_idcode()
    if xc3s200a.get_idcode() != xc3s200a._IDCODE:
        print 'ERROR'
    else:
        print 'SUCCESS'

    xsusb.set_prog(1)
    xsusb.set_prog(0)
    xsusb.set_prog(1)
    time.sleep(0.03)
        
    print "Status =",xc3s200a.get_status()
    t = time.clock()
    xc3s200a.configure(bitstream='test_board_jtag.bit')
    t = time.clock() - t
    print "Time to download bitstream = %fs" % t 
#    print "DONE =",xc3s200a.get_status()
    
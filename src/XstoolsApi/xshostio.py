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
Base object for performing I/O between XESS board and host PC.
'''

from xsjtag import *

_DEFAULT_XSUSB_ID = 0
_DEFAULT_MODULE_ID = 255

class XsHostIo:

    def __init__(self, xsjtag_port=None, xsusb_id=_DEFAULT_XSUSB_ID, module_id=_DEFAULT_MODULE_ID):
        self._xsusb_id = xsusb_id
        self._module_id = module_id
        if type(module_id) == type(1):
            self._module_id = XsBitarray.from_int(module_id, 8)
        if xsjtag_port == None:
            self._xsusb_port = XsUsb(xsusb_id)
            self._xsjtag_port = XsJtag(self._xsusb_port)
        else:
            self._xsjtag_port = xsjtag_port
        self.initialize()
            
    def initialize(self):
        assert self._xsjtag_port != None
        self._xsjtag_port.reset_tap()
        self._xsjtag_port.go_thru_tap_states(
            [
            'run_test_idle',
            'select_dr_scan',
            'select_ir_scan',
            'capture_ir',
            'shift_ir'
            ]
        )
        self.user_instr = XsBitarray('000010'[::-1])
        self._xsjtag_port.shift_tdi(tdi=self.user_instr, do_exit_shift=True, do_flush=True)
        self._xsjtag_port.go_thru_tap_states(
            [
            'update_ir',
            'select_dr_scan',
            'capture_dr',
            'shift_dr'
            ]
        )
        
    def reset(self):
        self.initialize()
        
    def send_rcv(self, payload, num_result_bits):
        print 'Send ', payload.length() , ' bits. Receive ', num_result_bits , ' bits.'
        num_payload_bits = XsBitarray.from_int(payload.length() + num_result_bits, 32)
        tdi_bits = XsBitarray()
#        tdi_bits.extend([self._module_id[::-1], num_payload_bits[::-1], payload])
        tdi_bits.extend(self._module_id[::-1])
        tdi_bits.extend(num_payload_bits[::-1])
        tdi_bits.extend(payload)
        print self._module_id, num_payload_bits, payload
        print tdi_bits.length(), tdi_bits
        self._xsjtag_port.shift_tdi(tdi=tdi_bits, do_exit_shift=False, do_flush=True)
        tdo_bits = self._xsjtag_port.shift_tdo(num_result_bits, do_exit_shift=False)
        return tdo_bits

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
JTAG interface through XESS USB interface.
'''

from xsbitarray import *
from xsusb import XsUsb

class XsJtag:

    _ENDIAN = 'big'

    _next_tap_state = {
        'invalid_tap_state' : [ 'invalid_tap_state', 'invalid_tap_state' ],
        'test_logic_reset'  : ['run_test_idle'     , 'test_logic_reset' ],
        'run_test_idle'     : ['run_test_idle'     , 'select_dr_scan'],
        'select_dr_scan'    : ['capture_dr'        , 'select_ir_scan'],
        'select_ir_scan'    : ['capture_ir'        , 'test_logic_reset'],
        'capture_dr'        : ['shift_dr'          , 'exit1_dr'],
        'capture_ir'        : ['shift_ir'          , 'exit1_ir'],
        'shift_dr'          : ['shift_dr'          , 'exit1_dr'],
        'shift_ir'          : ['shift_ir'          , 'exit1_ir'],
        'exit1_dr'          : ['pause_dr'          , 'update_dr'],
        'exit1_ir'          : ['pause_ir'          , 'update_ir'],
        'pause_dr'          : ['pause_dr'          , 'exit2_dr'],
        'pause_ir'          : ['pause_ir'          , 'exit2_ir'],
        'exit2_dr'          : ['shift_dr'          , 'update_dr'],
        'exit2_ir'          : ['shift_ir'          , 'update_ir'],
        'update_dr'         : ['run_test_idle'     , 'select_dr_scan'],
        'update_ir'         : ['run_test_idle'     , 'select_dr_scan']
    }

    def __init__(self, port=None):
        self._port = port
        self._tap_state = 'invalid_tap_state'
        self._tdi_bits = XsBitarray()
        self._tms_bits = XsBitarray()
        
    def _buffer_is_empty(self):
        return self._tdi_bits.length()==0 and self._tms_bits.length()==0
        
    def go_thru_tap_states(self, states):
        assert self._buffer_is_empty()
        for next_state in states:
            assert (next_state == self._next_tap_state[self._tap_state][0] 
                 or next_state == self._next_tap_state[self._tap_state][1])
            self.shift_tms(next_state == self._next_tap_state[self._tap_state][1])
        self.flush()
        
    def shift_tms(self, tms):
        self._tms_bits.append(tms)
        print self._tap_state,
        self._tap_state = self._next_tap_state[self._tap_state][tms]
        print ' => ', self._tap_state
        
    def shift_tdi(self, tdi, do_exit_shift=False, do_flush=True):
        assert self._tms_bits.length() == 0
        assert self._tap_state == 'shift_dr' or self._tap_state == 'shift_ir'
        if type(tdi) != type(XsBitarray()):
            tdi = XsBitarray([tdi])
        self._tdi_bits.extend(tdi)
        do_exit_shift and self.shift_tms(1)
        do_flush and self.flush()
        
    def shift_tdo(self, num_bits, do_exit_shift=False):
        if num_bits == 0:
            return XsBitarray()
        assert self._buffer_is_empty()
        assert self._tap_state == 'shift_dr' or self._tap_state == 'shift_ir'
        if do_exit_shift == True:
            tdo_bits = self.shift_tdo(num_bits=num_bits-1, do_exit_shift=False)
            self.shift_tms(1)
            self._tms_bits = XsBitarray()
            cmd = self._make_jtag_cmd_hdr(num_bits=1, flags=XsUsb.GET_TDO_MASK | XsUsb.TMS_VAL_MASK)
            self._port.write(cmd)
            buffer = self._port.read(1)
            bits = XsBitarray()
            bits.frombytes(buffer.tostring())
            bits.bytereverse()
            tdo_bits.extend(bits[-1:])
        else:
            cmd = self._make_jtag_cmd_hdr(num_bits=num_bits, flags=XsUsb.GET_TDO_MASK)
            self._port.write(cmd)
            num_bytes = int((num_bits+7)/8)
            num_extra_bits = num_bytes * 8 - num_bits
            buffer = self._port.read(num_bytes)
            bits = XsBitarray()
            bits.frombytes(buffer.tostring())
            bits.bytereverse()
            tdo_bits = bits[:num_bits]
        return tdo_bits[::-1]
        
    def reset_tap(self):
        assert self._buffer_is_empty()
        for i in range(0,5):
            self.shift_tms(1)
        self.flush()
        self._tap_state = 'test_logic_reset'
        
    def runtest(self, num_tcks):
        cmd = bytearray([
            XsUsb.RUNTEST_CMD, 
            num_tcks       & 0xff,
            (num_tcks>>8)  & 0xff,
            (num_tcks>>16) & 0xff,
            (num_tcks>>24) & 0xff
        ])
        self._port.write(cmd)
        response = self._port.read(5)
        assert response[0] == XsUsb.RUNTEST_CMD
        
    def _make_jtag_cmd_hdr(self, num_bits=0, flags=0):
        return bytearray([
            XsUsb.JTAG_CMD, 
            num_bits & 0xff,
            (num_bits>>8) & 0xff,
            (num_bits>>16) & 0xff,
            (num_bits>>24) & 0xff,
            flags
        ])
        
    def flush(self):
        assert not self._buffer_is_empty()
        assert self._port is not None
        
        if self._tdi_bits.length() == 0:
            buffer = self._make_jtag_cmd_hdr(num_bits=self._tms_bits.length(),flags=XsUsb.PUT_TMS_MASK)
            buffer.extend(self._tms_bits.to_usb_buffer())
        else:
            if self._tms_bits.length() == 0:
                buffer = self._make_jtag_cmd_hdr(num_bits=self._tdi_bits.length(),flags=XsUsb.PUT_TDI_MASK)
                buffer.extend(self._tdi_bits.to_usb_buffer())
            else:
                if self._tms_bits.length() == self._tdi_bits.length():
                    buffer = self._make_jtag_cmd_hdr(num_bits=self._tdi_bits.length(),
                                flags=(XsUsb.PUT_TMS_MASK | XsUsb.PUT_TDI_MASK))
                    tms_buffer = self._tms_bits.to_usb_buffer()
                    tdi_buffer = self._tdi_bits.to_usb_buffer()
                    tms_tdi_buffer = bytearray(len(tms_buffer) + len(tdi_buffer))
                    tms_tdi_buffer[::2]  = tms_buffer
                    tms_tdi_buffer[1::2] = tdi_buffer
                    buffer.extend(tms_tdi_buffer)
                elif self._tms_bits.length() == 1:
                    last_tms_bit = self._tms_bits.pop()
                    last_tdi_bit = self._tdi_bits.pop()
                    assert self._tms_bits.length()==0
                    assert self._tdi_bits.length()!=0
                    self.flush()
                    self._tms_bits.append(last_tms_bit)
                    self._tdi_bits.append(last_tdi_bit)
                    self.flush()
                    return
                else:
                    assert 1==0
        self._port.write(buffer)
        self._tms_bits = XsBitarray()
        self._tdi_bits = XsBitarray()

        
if __name__ == '__main__':
    print '#XSUSB = %d' % XsUsb.get_num_xsusb()
    xsusb = XsUsb()
    xsjtag = XsJtag(xsusb)
    xsjtag.reset_tap()
    xsjtag.go_thru_tap_states(
            [
            'run_test_idle',
            'select_dr_scan',
            'select_ir_scan',
            'capture_ir',
            'shift_ir'
            ]
        )
    idcode_instr = XsBitarray('001001'[::-1])
    xsjtag.shift_tdi(idcode_instr, do_exit_shift=True, do_flush=True)
    xsjtag.go_thru_tap_states(
            [
            'update_ir',
            'select_dr_scan',
            'capture_dr',
            'shift_dr'
            ]
        )
    idcode = xsjtag.shift_tdo(32, do_exit_shift=False)
    print idcode
    assert idcode[4:].to01() == '0010001000011000000010010011'
    xsjtag.runtest(1000)
    print '\n***Test passed!***'
        
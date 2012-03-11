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
Object for forcing inputs and reading outputs from a device-under-test (DUT).
'''

from xshostio import *

class XsDutIo(XsHostIo):
    _NOP_OPCODE   = XsBitarray('00'[::-1])
    _SIZE_OPCODE  = XsBitarray('01'[::-1])
    _WRITE_OPCODE = XsBitarray('10'[::-1])
    _READ_OPCODE  = XsBitarray('11'[::-1])
    _SIZE_RESULT_LENGTH = 16

    def __init__(self, xsjtag_port=None, xsusb_id=0, module_id=255, in_widths=None, out_widths=None):
#        super(XsDutIo,self).__init__(xsjtag_port=xsjtag_port, xsusb_id=xsusb_id, module_id=module_id)
        XsHostIo.__init__(self, xsjtag_port=xsjtag_port, xsusb_id=xsusb_id, module_id=module_id)
        self._num_inputs, self._num_outputs = self._get_io_widths()
        print self._num_inputs, self._num_outputs
        if in_widths == None:
            self._in_widths = [self._num_inputs]
        else:
            self._in_widths = in_widths
            total_width = 0
            for w in self._in_widths:
                total_width += w
            assert total_width == self._num_inputs
        if out_widths == None:
            self._out_widths = [self._num_outputs]
        else:
            self._out_widths = out_widths
            total_width = 0
            for w in self._out_widths:
                total_width += w
            assert total_width == self._num_outputs
        
    def _get_io_widths(self):
        SKIP_CYCLES = 1
        params = self.send_rcv(payload=self._SIZE_OPCODE, 
                num_result_bits=self._SIZE_RESULT_LENGTH + SKIP_CYCLES)
        params = params[:-SKIP_CYCLES]
        input_width = params[self._SIZE_RESULT_LENGTH/2:].to_int()
        output_width = params[:self._SIZE_RESULT_LENGTH/2].to_int()
        return input_width, output_width
        
    def read(self):
        SKIP_CYCLES = 1
        result = self.send_rcv(payload=self._READ_OPCODE,
                num_result_bits=self._num_inputs + SKIP_CYCLES)
        result = result[SKIP_CYCLES:]
        assert result.length() == self._num_inputs
        print 'Read result = ', result
        if len(self._out_widths) == 1:
            return result
        else:
            outputs = []
            for w in self._out_widths:
                outputs.append(result[:w])
                result = result[w:]
            return outputs
            
    Read = read
        
    def write(self, *inputs):
        assert len(inputs) != 0
        assert len(inputs) == self.num_inputs
        payload = XsBitarray(self._WRITE_OPCODE)
        for i, w in inputs, self._input_widths:
            payload.extend(XsBitarray.from_int(i, w))
        assert payload.length() > 0
        self.send_rcv(payload=payload, num_result_bits=0)
        
    Write = write

    def execute(self, *inputs): 
        self.write(*inputs)
        return self.read()
        
    Exec = execute

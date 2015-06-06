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
Object for reading and writing data to/from RAM.
"""

import logging
from xshostio import *


class XsRamIo(XsHostIo):

    """Object for reading and writing data to/from RAM."""

    # DUT opcodes.

    _NOP_OPCODE = XsBitarray('00'[::-1])
    _READ_OPCODE = XsBitarray('11'[::-1])  # Read DUT outputs.
    _WRITE_OPCODE = XsBitarray('10'[::-1])  # Write to DUT inputs.
    _SIZE_OPCODE = XsBitarray('01'[::-1])  # Get RAM address & data widths.
    _SIZE_RESULT_LENGTH = 16  # Length of _SIZE_OPCODE result.

    def __init__(
        self,
        xsusb_id=DEFAULT_XSUSB_ID,
        module_id=DEFAULT_MODULE_ID,
        xsjtag=None,
        ):
        """Setup a RAM I/O object.
        
        xsusb_id = The ID for the USB port.
        module_id = The ID for the DUT I/O module in the FPGA.
        xsjtag = The Xsjtag USB port object. (Use this if not using xsusb_id.)
        """

        # Setup the super-class object.
        XsHostIo.__init__(self, xsusb_id=xsusb_id, module_id=module_id,
                          xsjtag=xsjtag)

        # Get the widths of the RAM address and data.
        (self.addr_width, self.data_width) = self._get_ram_widths()
        assert self.data_width != 0
        assert self.addr_width != 0
        logging.debug('RAM data width = %d' % self.data_width)
        logging.debug('RAM address width = %d' % self.addr_width)

    def _get_ram_widths(self):
        """Return the (addr_width, data_width) of the DUT."""

        SKIP_CYCLES = 1  # Skip cycles between issuing command and reading back result.

        # Send the opcode and then read back the bits with the DUT's #inputs and #outputs.
        params = self.send_rcv(payload=self._SIZE_OPCODE,
                               num_result_bits=self._SIZE_RESULT_LENGTH
                               + SKIP_CYCLES)
        params = params[SKIP_CYCLES:]  # Remove the skipped cycles.

        # The address width is in the first half of the bit array.
        addr_width = params[:self._SIZE_RESULT_LENGTH / 2].to_int()

        # The data width is in the last half of the bit array.
        data_width = params[self._SIZE_RESULT_LENGTH / 2:].to_int()
        return (addr_width, data_width)

    def read(self, start_address, num_reads):
        """Return a list of RAM data word bit arrays starting from the given address."""

        SKIP_CYCLES = self.data_width  # Skip cycles between issuing command and reading back result.

        # Send the READ_OPCODE and the starting address and then read back the RAM data values.
        payload = XsBitarray(self._READ_OPCODE)
        payload.extend(XsBitarray.from_int(start_address,
                       self.addr_width))
        result = self.send_rcv(payload=payload,
                               num_result_bits=self.data_width
                               * num_reads + SKIP_CYCLES)
        assert result.length() == self.data_width * num_reads + SKIP_CYCLES
        logging.debug('Read result = ' + repr(result))
        if num_reads == 1:
            # Return a single bit vector if there's only a single read.
            return result[SKIP_CYCLES:]
        else:
            # Otherwise, return a list of RAM data values.
            data = [result[i:i+self.data_width] for i in range(SKIP_CYCLES,result.length(),self.data_width)]
            #data = [result[i*self.data_width:(i+1)*self.data_width] for i in range(0,num_reads)]
            return data

    def write(self, start_address, data):
        """Send a list of data bit arrays to the RAM starting at the given address."""

        # Start the payload with the WRITE_OPCODE and the starting address.
        payload = XsBitarray(self._WRITE_OPCODE)
        payload.extend(XsBitarray.from_int(start_address,
                       self.addr_width))

        # Concatenate the data bit arrays to the payload.
        for w in data:
            if isinstance(w, (int, long)):
                # Convert the integer to a bit array and concatenate it.
                payload.extend(XsBitarray.from_int(w, self.data_width))
            elif isinstance(w, bitarray):
                # Assume it's a bit array, so just concatenate it.
                payload.extend(w)
            else:
                raise(XsMajorError("Writing unsupported data type: %s." % type(w)))
        assert payload.length() > self._WRITE_OPCODE.length()

        # Send the payload to write the bit arrays into the RAM.
        self.send_rcv(payload=payload, num_result_bits=0)


if __name__ == '__main__':
    # from pylab import *
    # import pickle
    # ram = XsRamIo(0,255)
    # print "\nAddress width = %d, Data width = %d" % ram._get_ram_widths()
    # sample_rate = 48000;
    # sample_period = 1.0/sample_rate
    # length = sample_rate * 5
    # rd_data = ram.read(0,length)
    # signal = [s[:-1].integer for s in rd_data]
    # t = arange(0.0, length * sample_period, sample_period)
    # peak = [rd_data[i][:-1].integer for i in range(0,len(rd_data)) if rd_data[i][-1]==1]
    # peak_t = [i*sample_period for i in range(0,len(rd_data)) if rd_data[i][-1]==1]
    # pickle.dump(signal, open("audio.p","wb"))
    # decimation = 1
    # plot(t[::decimation],signal[::decimation],"b-",peak_t,peak,"r o")
    # xlabel('time')
    # ylabel('audio')
    # title('audio waveform')
    # grid(True)
    # show()
    # exit(0)
    
    import random
    
    ram = XsRamIo(0,255)
    print "\nAddress width = %d, Data width = %d" % ram._get_ram_widths()
    start = 0
    end = 0xff
    wr_data = [random.randint(0,0xffff) for a in range(start,end+1)]
    ram.write(start,wr_data)
    rd_data = ram.read(start,end-start+1)
#    rd_data = rd_data[1:]
    wr_rd_data = zip(wr_data, rd_data)
    for (wr,rd) in wr_rd_data:
        if wr != rd.unsigned:
            print "Error: wr=%x, rd=%x" % (wr,rd.unsigned)
    exit(0)
    
    wr_data = [2*a for a in addr]
#    for a in addr:
#        ram.write(a,[a])
    ram.write(5, wr_data)
#    ram.write(0, wr_data)
#    ram.write(0, wr_data)
#    print "write done"
#    rd_data = ram.read(addr[0],len(addr))
#    rd_data = [0] * len(addr)
#    for a in addr:
#        rd_data[a] = ram.read(a,1)
    rd_data = ram.read(addr[0],len(addr))
    print "read done"
    for a in addr:
        if a & 0x7 == 0:
            print "\n%04x:" % a,
        dr = rd_data[a].unsigned
        print "%02x %02x" % ((dr>>8)&0xff, dr&0xff),
    exit(0)
    print len(wr_data), len(rd_data)
    wr_rd_data = zip(wr_data, rd_data)
    print "read and write data zipped"
    bit_errors = 0
    for a in addr:
        dr = rd_data[a]
        dw = wr_data[a]
        bit_errors |= (dr.unsigned ^ dw)
        if dr.unsigned != dw:
            print "Error: %04x != @(%04x) %04x; %04x %04x" % (dr.unsigned, a, dw, ram.read(a,1).unsigned, ram.read(a,1).unsigned)
            # for i in range(0,10):
                # ram.write(dw,[dw])
                # print ram.read(dw,1).unsigned
            # exit(0)
    bstr = lambda n, l=16: n<0 and binarystr((2L<<l)+n) or n and bstr(n>>1).lstrip('0')+str(n&1) or '0'
    print "bit_errors = %s" % bstr(bit_errors)
            
        
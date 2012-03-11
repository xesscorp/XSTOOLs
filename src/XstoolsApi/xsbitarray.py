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
XESS extensions to bitarray object.
'''

from bitarray import bitarray

class XsBitarray(bitarray):

    '''Class for storing and manipulating bits.'''

    def __init__(self, initial=None):
        bitarray.__init__(initial, endian='big')
    
    @staticmethod
    def from_int(num, num_of_bits=32):
        assert num < (1<<num_of_bits)
        return XsBitarray(bin(num | (1<<num_of_bits))[3:])
        
    def to_int(self):
        return int(self.to01(),2)
        
    def to_usb_buffer(self):
        tmp = XsBitarray()
        tmp.frombytes(self.tobytes())
        tmp.bytereverse()
        return tmp.tobytes()
    
    def __setattr__(self, name, val):
        if name == 'unsigned' or name == 'int':
            self = XsBitarray.from_int(val, len(self))
        elif name == 'string':
            self = XsBitarray(val)
        return val
        
    def __getattr__(self, name):
        if name == 'unsigned':
            val = self.to_int()
        elif name == 'int':
            val = self[1:].to_int()
            if self[0] == 1:
                val *= -1
        elif name == 'string':
            val = self.to01()
        return val

        
if __name__ == '__main__':
    xsbits = XsBitarray('1010101')
    print str(xsbits)
    xsbits = XsBitarray.from_int(45)
    print str(xsbits)
    print xsbits.to01()
    print xsbits.to_int()
    xsbits = XsBitarray.from_int(27,8)
    print str(xsbits)
    print xsbits.to_int()
    

            
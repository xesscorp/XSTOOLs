# File originally from http://excamera.com/sphinx/fpga-xess-python.html
# Added BitstreamString class -- HP

import struct
import array
import os

class Bitstream:
    """
    Simple bitstream specified as a count and integer value.
    """
    def __init__(self, n, val):
        self.n = n
        self.val = val

    def __iter__(self):
        def getbits():
            for i in range(self.n):
                yield (self.val >> i) & 1
        return getbits()

    def __len__(self):
        return self.n

class BitstreamHex:
    """
    Bitstream specified as a hex string
    """
    def __init__(self, s):
        self.s = s

    def __iter__(self):
        def getbits():
            for hd in self.s:
                b = int(hd, 16)
                yield (b >> 3) & 1
                yield (b >> 2) & 1
                yield (b >> 1) & 1
                yield (b >> 0) & 1
        return getbits()

    def __len__(self):
        return len(self.s) * 4

class BitstreamString:
    """
    Bitstream specified as a byte string
    """
    def __init__(self, s):
        self.s = array.array('B', s)

    def __iter__(self):
        def getbits():
            for b in self.s:
                yield (b >> 7) & 1
                yield (b >> 6) & 1
                yield (b >> 5) & 1
                yield (b >> 4) & 1
                yield (b >> 3) & 1
                yield (b >> 2) & 1
                yield (b >> 1) & 1
                yield (b >> 0) & 1
        return getbits()

    def __len__(self):
        return len(self.s) * 8

    def tostring(self):
        return self.s.tostring()

class BitFile:
    def __init__(self, bitfilename):
        self.bit = open(bitfilename, "rb")

        def getH(fi):
            return struct.unpack(">H", self.bit.read(2))[0]
        def getI(fi):
            return struct.unpack(">I", self.bit.read(4))[0]

        self.bit.seek(getH(self.bit), os.SEEK_CUR)
        assert getH(self.bit) == 1

        # Search for the data section in the .self.bit file...
        while True:
            ty = ord(self.bit.read(1))
            if ty == 0x65:
                break
            length = getH(self.bit)
            self.bit.seek(length, os.SEEK_CUR)
        self.fieldLength = getI(self.bit)
        print "bitfile %s loaded, %d bytes" % (bitfilename, self.fieldLength)

    def __len__(self):
        return self.fieldLength * 8

    def __iter__(self):
        def getbits():
            for i in range(self.fieldLength):
                b = ord(self.bit.read(1))
                # print "File %02x" % b
                for j in range(8):
                    yield (b >> (7-j)) & 1
        return getbits()

    def tostring(self):
        return self.bit.read(self.fieldLength)

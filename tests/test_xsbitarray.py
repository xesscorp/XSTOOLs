import unittest

from xstools.xsbitarray import XsBitArray


class TestXSBitArray(unittest.TestCase):
    def test_head(self):
        arr = XsBitArray('0b01')
        self.assertEqual(arr.head(), XsBitArray('0b1'))
        self.assertNotEqual(arr.head(), XsBitArray('0b0'))

    def test_tail(self):
        arr = XsBitArray('0b01')
        self.assertEqual(arr.tail(), XsBitArray('0b0'))
        self.assertNotEqual(arr.tail(), XsBitArray('0b1'))

    def test_to_usb(self):
        a_arr = XsBitArray('0b00010')
        b_arr = XsBitArray('0b1111001')
        c_arr = a_arr + b_arr
        self.assertEqual(c_arr, XsBitArray('0xf22'))
        self.assertEqual(c_arr.to_usb(), b'"\x0f')

    def test_to_intel_hex(self):
        arr = XsBitArray('0b01')
        hex_arr = arr.to_intel_hex()
        binstr = hex_arr.tobinstr()
        # Getting an error here in IntelHex 2.1 on Python 2
        # Traceback (most recent call last):
        #   File "/Users/xilinx/code/XSTOOLs/tests/test_xsbitarray.py", line 27, in test_to_intel_hex
        #     binstr = hex_arr.tobinstr()
        #   File "/Users/xilinx/.local/lib/python2.7/site-packages/intelhex/__init__.py", line 375, in tobinstr
        #     return self._tobinstr_really(start, end, pad, size)
        #   File "/Users/xilinx/.local/lib/python2.7/site-packages/intelhex/__init__.py", line 378, in _tobinstr_really
        #     return asbytes(self._tobinarray_really(start, end, pad, size).tostring())
        #   File "/Users/xilinx/.local/lib/python2.7/site-packages/intelhex/__init__.py", line 352, in _tobinarray_really
        #     bin.append(self._buf.get(i, pad))
        # TypeError: an integer is required
        # TODO: What should this output?
        self.assertEqual(binstr, b'@')

import unittest

from intelhex import IntelHex

from xstools.xilbitstr import XilinxBitstream
from xstools.xsboard import Xula2lx25, Xula2lx9, Xula50, Xula200, Xula2, Xula


class ExampleTest(unittest.TestCase):
    def test_bitstreams(self):
        # Why does each board bitstream have a characteristic length?
        board_bit_lengths = [
            (Xula2lx25, 6411696),
            (Xula2lx9, 2724832),
            (Xula50, 437312),
            (Xula200, 1196128)
        ]
        bitstreams = ['cfg_flash', 'sdram', 'test']
        for b, exp_bit_len in board_bit_lengths:
            for bs in bitstreams:
                xbs = XilinxBitstream()
                fp = getattr(b, bs + '_bitstream')
                xbs.from_file(fp)
                self.assertEqual(len(xbs.bits), exp_bit_len)
                ih = xbs.to_intel_hex()
                self.assertEqual(ih.minaddr(), 0)
                self.assertEqual(ih.maxaddr(), (exp_bit_len + 120) // 8)

    def test_intel_hex(self):
        boards = [Xula2, Xula]
        for b in boards:
            hex_fp = b.firmware
            ih = IntelHex(hex_fp)
            self.assertEqual(ih.minaddr(), 2048)
            self.assertEqual(ih.maxaddr(), 3145741)

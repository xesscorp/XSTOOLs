import unittest
from intelhex import IntelHex
import xstools.xsboard

class Sdramtest(unittest.TestCase):
    def setUp(self):
        self.board=xstools.xsboard.Xula2lx25(0)
    
    def test_readwrite(self):
        '''
        test read and write sdram

        writes 13 zeroes to sdram, hereafter reads 13 values
        from sdram and checks equality
        '''
        keys=range(0,14)
        values=14*[0]
        data=IntelHex()
        data.fromdict(dict(zip(keys,values)))
        self.board.write_sdram(data,0,len(keys)-1)
        result=self.board.read_sdram(0,len(keys)-1)
        self.assertEqual(data.todict(),result.todict())

if __name__ == '__main__':
    unittest.main()


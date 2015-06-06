# Python script to upload a binary file from the XuLA FPGA.

import sys
import time
import string

from xula import XuLA, elapsed
from bitstream import Bitstream, BitstreamHex, BitFile

def main(bitfilename, loaddr, hiaddr):
    x = XuLA()
    chain = x.querychain()
    if chain != [0x02218093]:
       print "Expected single XC3S200A, but chain is", chain
    print "OK, found DEVICEID for XC3S200A"
    t = time.time()
    x.read_flash(bitfilename, string.atoi(loaddr, 0), string.atoi(hiaddr, 0), True)
    t = time.time() - t
    print "read complete, took", elapsed(t)

if __name__ == "__main__":
    print "XuLA Flash uploader"
    if len(sys.argv) != 4:
        print "usage: python %s <bitfile> <loaddr> <hiaddr>" % sys.argv[0]
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])

import sys
import serial

# Uncomment this path when using local development version of xstools.
sys.path.insert(0, r'C:\xesscorp\products\xstools')

import xstools.xscomm

xscomm = xstools.xscomm.XsComm(xsusb_id=0, module_id=240)
sercomm = serial.Serial(7)
print sercomm
sercomm.writeTimeout = 0
print "Serial port = ", sercomm.name

#xscomm.reset()

c = 0
sz = 8
while True:
    xscomm.send([b % 256 for b in range(c,c+sz)])
    rcv = xscomm.receive(sz)
    s = "%d: " % c
    for d in rcv:
       s += "%02x " % d.unsigned
    s += "\n"
    print s,
    sercomm.write(s)
    c = (c+sz) % 256

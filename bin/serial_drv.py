import sys
import serial

sercomm = serial.Serial(8)
print sercomm
sercomm.writeTimeout = 0
print "Serial port = ", sercomm.name

while(True):
    sercomm.write("b")

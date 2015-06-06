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
# *   (c)2011 - X Engineering Software Systems Corp. (www.xess.com)
# ***********************************************************************************/

import sys
from XstoolsApi import *  # Import the funcs/objects for the PC <=> FPGA link.
from random import *  # Import some random number generator routines.

print '''
##################################################################
# Test the SD card on the XuLA-2 using the PC to drive the
# SPI lines directly.
##################################################################
'''

def pulse_clock(mosi=1, cs=0):
  miso = sdcard.execute(cs, 1, mosi) # Raise clock, then get MISO from SD card.
  sdcard.write(cs, 0, mosi) # Lower clock.
#  sdcard.write(cs, 1, mosi)
#  return sdcard.execute(cs,0,mosi)
  return miso # Return MISO as a single- bit array.

def select_sdcard():
  sdcard.write(0, 0, 1) # Lower SD card chip-select, keep sclk low and mosi high.
  
def deselect_sdcard():
  sdcard.write(1, 0, 1) # Raise SD card chip-select, keep sclk low and mosi high.
  pulse_clock(mosi=1, cs=1) # Pulse sclk once to let SD card see chip-select is high? Tests show this is needed. 
  
def init_sdcard():
  for i in range(0, 160):
    pulse_clock(1, 1)
  while send_cmd(0,0,0x95).unsigned != 0x01:
    deselect_sdcard()
  deselect_sdcard()
  print send_cmd(8,0x1aa,0x87)
  rx_byte()
  rx_byte()
  rx_byte()
  rx_byte()
  deselect_sdcard()
  while True:
    print send_cmd(55,0,0xFF)
    deselect_sdcard()
#    r1 = send_cmd(41,0,0xFF)
    r1 = send_cmd(41,0x40000000,0xFF)
    deselect_sdcard()
    print r1
    if r1[0] == False:
      break
  
def tx(bits):
  bits.reverse()
  for b in bits:
    pulse_clock(mosi = b)
    
def tx_byte(byte):
  tx(XsBitarray().from_int(byte,8))
    
def rx():
  bits = XsBitarray()
  for i in range(0,8):
    bits += pulse_clock()
  bits.reverse()
  return bits
  
def rx_byte():
  return rx().unsigned
    
def wait_for_R1():
  r1 = XsBitarray()
  for i in range(0, 20):
    if pulse_clock().int == 0:
      for j in range(0, 7):
        r1 += pulse_clock()
      r1.reverse()
      return r1
  raise Exception("Failed to find R1 response!")
    
def send_cmd(cmd, address=0, crc=0xff):
  select_sdcard()
  bits = XsBitarray().from_int(crc, 8) + XsBitarray().from_int(address, 32) + XsBitarray().from_int(cmd|0x40, 8)
  tx(bits)
  r1 = wait_for_R1()
  return r1
  
def tx_block(address, data):
  r1 = send_cmd(cmd=24, address=address)
  print r1
  if r1.int != 0:
    raise Exception("Write error: %02x" % r1.int)
  tx_byte(0xff)
  tx_byte(0xfe)
  for byte in data:
    tx_byte(byte)
  tx_byte(0xff)
  tx_byte(0xff)
  pulse_clock()
  data_response = rx_byte()
  if data_response & 0x1f != 0x05:
    raise Exception("Write block response is wrong: %02x" % data_response)
  print "Waiting for write to finish"
  while rx_byte()==0:
    pass
  deselect_sdcard()
  

def rx_block(address):
  r1 = send_cmd(cmd=17, address=address)
  print r1
  if r1.int != 0:
    raise Exception("Read error: %02x" % r1.int)
  token = rx_byte()
  while token == 0xff:
    token = rx_byte()
  if token != 0xfe:
    raise Exception("Read block data token is wrong: %02x" % token)
  data = []
  for i in range(0,512):
    data.append(rx_byte())
  crc = []
  crc.append(rx_byte())
  crc.append(rx_byte())
  deselect_sdcard()
  return (data, crc)
  
    
USB_ID = 0  # USB port index for the XuLA board connected to the host PC.
SDCARD_ID = 255  # This is the identifier for the SD card interface in the FPGA.

# Create a subtractor intfc obj with three 1-bit inputs and one 1-bit output.
sdcard = XsDut(USB_ID, SDCARD_ID, [1,1,1], [1])

block_address = 512 * 0
print "Initializing SD card...",
init_sdcard()
print "done"
wr_data = [randint(0,255) for b in range(0,512)]
print "Writing data...",
tx_block(block_address, wr_data)
print "done"
print "Reading data...",
(rd_data, crc) = rx_block(block_address)
print "done"
print rd_data
print crc
for (wr, rd) in zip(wr_data, rd_data):
  if wr != rd:
    print "Data error: %02x != %02x" % (wr, rd) 
sys.exit()

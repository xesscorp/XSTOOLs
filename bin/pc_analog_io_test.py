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

from XstoolsApi import *  # Import the funcs/objects for the PC <=> FPGA link.
from xsusb   import *

print '''
##################################################################
# This program Does a test of AIO pins by capturing their value and
# printing them out.
# on the XuLA board that has been programmed to act as a subtractor.
# This test has nothing to do with the FPGA side of the Xula board
# This only uses the PIC micro
# THe main values that matter are specified in firmware/user/user.c
    // Disable analog functions of the I/O pins.
    // Enable the one for RB5 and RC2
    ANSELbits.ANS6  = 1;
    ANSELHbits.ANS11 = 1;
    TRISCbits.TRISC2  = 1;              // Make the pin input analog
    TRISBbits.TRISB5  = 1;              // Make the pin input analog

    REFCON0bits.FVR1EN= 1;              // Enable the FVR
    REFCON0bits.FVR1S1= 1;              // Make the FVR 2.048 (nominal)
    REFCON0bits.FVR1S0= 0;              // Make the FVR 2.048 (nominal)
    ADCON2bits.ADCS   = 0x6;            // Select F/32 for ADC clock source
    ADCON2bits.ACQT   = 0x5;            // Select T12 for ACQT
    ADCON1bits.NVCFG0 = 0;              // Set PVCFG to FVR and NVCFG to VSS
    ADCON1bits.NVCFG1 = 0;              // Set PVCFG to FVR and NVCFG to VSS
    ADCON1bits.PVCFG0 = 0;              // Set PVCFG to FVR and NVCFG to VSS
    ADCON1bits.PVCFG1 = 1;              // Set PVCFG to FVR and NVCFG to VSS
    ADCON0bits.ADON   = 1;              // Turn the ADC on
    ADCON2bits.ADFM   = 1;              // Make the format right justified

You may want to changes these to suit your needs and then recompile the pic
firmware.
##################################################################
'''
myxsusb = XsUsb()
for i in range(0, 10):
    aio0_out = myxsusb.adc_aio0()
#    aio0 = aio0_out[1]*256+aio0_out[2]
    aio1_out = myxsusb.adc_aio1()
#    aio1 = aio1_out[1]*256+aio1_out[2]
#    print ' AIO0  = %x %x %x %x %d AIO1= %x %x %x %x %d' % (aio0_out[1],aio0_out[2],aio0_out[0],aio0 , aio0 , aio1_out[1],aio1_out[2],aio1_out[0],aio1 , aio1)
    print "aio0 = %f\taio1 = %f" % (aio0_out,aio1_out)
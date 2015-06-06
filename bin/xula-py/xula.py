# Class to access the XuLA board features
# File originally from http://excamera.com/sphinx/fpga-xess-python.html  
# Fixed load method so bitstreams generated with the "JTAG Clock" option will work -- HP
# Added flash uploader/downloader -- HP

import time
import usb
import sys
import struct
import array
import random

from jtag import Jtag, islast
from bitstream import *

# Definitions of commands sent in USB packets.

READ_VERSION_CMD       = 0x00  # Read the product version information.
READ_FLASH_CMD         = 0x01  # Read from the device flash.
WRITE_FLASH_CMD        = 0x02  # Write to the device flash.
ERASE_FLASH_CMD        = 0x03  # Erase the device flash.
READ_EEDATA_CMD        = 0x04  # Read from the device EEPROM.
WRITE_EEDATA_CMD       = 0x05  # Write to the device EEPROM.
READ_CONFIG_CMD        = 0x06  # Read from the device configuration memory.
WRITE_CONFIG_CMD       = 0x07  # Write to the device configuration memory.
ID_BOARD_CMD           = 0x31  # Flash the device LED to identify which device is being communicated with.
UPDATE_LED_CMD         = 0x32  # Change the state of the device LED.
INFO_CMD               = 0x40  # Get information about the USB interface.
SENSE_INVERTERS_CMD    = 0x41  # Sense inverters on TCK and TDO pins of the secondary JTAG port.
TMS_TDI_CMD            = 0x42  # Send a single TMS and TDI bit.
TMS_TDI_TDO_CMD        = 0x43  # Send a single TMS and TDI bit and receive TDO bit.
TDI_TDO_CMD            = 0x44  # Send multiple TDI bits and receive multiple TDO bits.
TDO_CMD                = 0x45  # Receive multiple TDO bits.
TDI_CMD                = 0x46  # Send multiple TDI bits.
RUNTEST_CMD            = 0x47  # Pulse TCK a given number of times.
NULL_TDI_CMD           = 0x48  # Send string of TDI bits.
PROG_CMD               = 0x49  # Change the level of the FPGA PROGRAM# pin.
SINGLE_TEST_VECTOR_CMD = 0x4a  # Send a single, byte-wide test vector.
GET_TEST_VECTOR_CMD    = 0x4b  # Read the current test vector being output.
SET_OSC_FREQ_CMD       = 0x4c  # Set the frequency of the DS1075 oscillator.
ENABLE_RETURN_CMD      = 0x4d  # Enable return of info in response to a command.
DISABLE_RETURN_CMD     = 0x4e  # Disable return of info in response to a command.
TAP_SEQ_CMD            = 0x4f  # Send multiple TMS & TDI bits while receiving multiple TDO bits.
FLASH_ONOFF_CMD        = 0x50  # Enable/disable the FPGA configuration flash.
RESET_CMD              = 0xff  # Cause a power-on reset.

# Definitions of commands sent after a USER JTAG instruction.

INSTR_NOP           = Bitstream(8, int( "00000000", 2)) # no operation
INSTR_RUN_DIAG      = Bitstream(9, int("000000011", 2)) # run board diagnostic; must be one bit longer than normal
INSTR_RAM_WRITE     = Bitstream(8, int( "00000101", 2)) # write data to RAM
INSTR_RAM_READ      = Bitstream(8, int( "00000111", 2)) # read data from RAM
INSTR_RAM_SIZE      = Bitstream(9, int("000001001", 2)) # get RAM organization; must be one bit longer than normal
INSTR_FLASH_ERASE   = Bitstream(9, int("000001011", 2)) # erase entire Flash chip; must be one bit longer than normal 
INSTR_FLASH_PGM     = Bitstream(8, int( "00001101", 2)) # program downloaded block of data into Flash
INSTR_FLASH_BLK_PGM = Bitstream(8, int( "00001111", 2)) # program downloaded block of data into Flash
INSTR_FLASH_READ    = Bitstream(8, int( "00010001", 2)) # read data from Flash
INSTR_FLASH_SIZE    = Bitstream(9, int("000010011", 2)) # get Flash organization; must be one bit longer than normal
INSTR_REG_WRITE     = Bitstream(8, int( "00010101", 2)) # write data to registers
INSTR_REG_READ      = Bitstream(8, int( "00010111", 2)) # read data from registers
INSTR_REG_SIZE      = Bitstream(9, int("000011001", 2)) # get register organization; must be one bit longer than normal
INSTR_CAPABILITIES  = Bitstream(9, int("011111111", 2)) # get capabilities of instruction execution unit; must be one bit longer than normal

# The length of the TDO register used to return information to the PC

TDO_LENGTH = 32

# Possible capabilities for the instruction execution unit.
# The lower and upper bytes are mirrors of each other, and bits are set
# in the middle two bytes to indicate if a given capability is present.

NO_CAPABILITIES          = 0xA50000A5
CAPABLE_RUN_DIAG_BIT     = 8
CAPABLE_RUN_DIAG_MASK    = 1 << CAPABLE_RUN_DIAG_BIT
CAPABLE_RAM_WRITE_BIT    = 9
CAPABLE_RAM_WRITE_MASK   = 1 << CAPABLE_RAM_WRITE_BIT
CAPABLE_RAM_READ_BIT     = 10
CAPABLE_RAM_READ_MASK    = 1 << CAPABLE_RAM_READ_BIT
CAPABLE_FLASH_WRITE_BIT  = 11
CAPABLE_FLASH_WRITE_MASK = 1 << CAPABLE_FLASH_WRITE_BIT
CAPABLE_FLASH_READ_BIT   = 12
CAPABLE_FLASH_READ_MASK  = 1 << CAPABLE_FLASH_READ_BIT
CAPABLE_REG_WRITE_BIT    = 13
CAPABLE_REG_WRITE_MASK   = 1 << CAPABLE_REG_WRITE_BIT
CAPABLE_REG_READ_BIT     = 14
CAPABLE_REG_READ_MASK    = 1 << CAPABLE_REG_READ_BIT

# Status codes from the instruction execution unit.

OP_INPROGRESS = 0x01230123
OP_PASSED     = 0x45674567
OP_FAILED     = 0x89AB89AB

def bytes(*b):
    return array.array('B', b).tostring()

def elapsed(t):
    seconds = t % 60
    minutes = int(t / 60) % 60
    hours = int(t / 3600)
    r = ""
    if hours > 0:
        r += "%d hours, " % hours
    if hours > 0 or minutes > 0:
        r += r + "%d minutes, " % minutes
    r += "%.3f seconds" % seconds
    return r

reverse_bits = [
    0x00, 0x80, 0x40, 0xc0, 0x20, 0xa0, 0x60, 0xe0, 0x10, 0x90, 0x50, 0xd0, 0x30, 0xb0, 0x70, 0xf0,
    0x08, 0x88, 0x48, 0xc8, 0x28, 0xa8, 0x68, 0xe8, 0x18, 0x98, 0x58, 0xd8, 0x38, 0xb8, 0x78, 0xf8,
    0x04, 0x84, 0x44, 0xc4, 0x24, 0xa4, 0x64, 0xe4, 0x14, 0x94, 0x54, 0xd4, 0x34, 0xb4, 0x74, 0xf4,
    0x0c, 0x8c, 0x4c, 0xcc, 0x2c, 0xac, 0x6c, 0xec, 0x1c, 0x9c, 0x5c, 0xdc, 0x3c, 0xbc, 0x7c, 0xfc,
    0x02, 0x82, 0x42, 0xc2, 0x22, 0xa2, 0x62, 0xe2, 0x12, 0x92, 0x52, 0xd2, 0x32, 0xb2, 0x72, 0xf2,
    0x0a, 0x8a, 0x4a, 0xca, 0x2a, 0xaa, 0x6a, 0xea, 0x1a, 0x9a, 0x5a, 0xda, 0x3a, 0xba, 0x7a, 0xfa,
    0x06, 0x86, 0x46, 0xc6, 0x26, 0xa6, 0x66, 0xe6, 0x16, 0x96, 0x56, 0xd6, 0x36, 0xb6, 0x76, 0xf6,
    0x0e, 0x8e, 0x4e, 0xce, 0x2e, 0xae, 0x6e, 0xee, 0x1e, 0x9e, 0x5e, 0xde, 0x3e, 0xbe, 0x7e, 0xfe,
    0x01, 0x81, 0x41, 0xc1, 0x21, 0xa1, 0x61, 0xe1, 0x11, 0x91, 0x51, 0xd1, 0x31, 0xb1, 0x71, 0xf1,
    0x09, 0x89, 0x49, 0xc9, 0x29, 0xa9, 0x69, 0xe9, 0x19, 0x99, 0x59, 0xd9, 0x39, 0xb9, 0x79, 0xf9,
    0x05, 0x85, 0x45, 0xc5, 0x25, 0xa5, 0x65, 0xe5, 0x15, 0x95, 0x55, 0xd5, 0x35, 0xb5, 0x75, 0xf5,
    0x0d, 0x8d, 0x4d, 0xcd, 0x2d, 0xad, 0x6d, 0xed, 0x1d, 0x9d, 0x5d, 0xdd, 0x3d, 0xbd, 0x7d, 0xfd,
    0x03, 0x83, 0x43, 0xc3, 0x23, 0xa3, 0x63, 0xe3, 0x13, 0x93, 0x53, 0xd3, 0x33, 0xb3, 0x73, 0xf3,
    0x0b, 0x8b, 0x4b, 0xcb, 0x2b, 0xab, 0x6b, 0xeb, 0x1b, 0x9b, 0x5b, 0xdb, 0x3b, 0xbb, 0x7b, 0xfb,
    0x07, 0x87, 0x47, 0xc7, 0x27, 0xa7, 0x67, 0xe7, 0x17, 0x97, 0x57, 0xd7, 0x37, 0xb7, 0x77, 0xf7,
    0x0f, 0x8f, 0x4f, 0xcf, 0x2f, 0xaf, 0x6f, 0xef, 0x1f, 0x9f, 0x5f, 0xdf, 0x3f, 0xbf, 0x7f, 0xff,
]

class XuLA(Jtag):

    # see ug332, Table 9-5 p 207:
    # Spartan-3 Boundary Scan Instructions
    EXTEST       = Bitstream(6, int("001111", 2))
    SAMPLE       = Bitstream(6, int("000001", 2))
    USER1        = Bitstream(6, int("000010", 2))
    USER2        = Bitstream(6, int("000011", 2))
    CFG_OUT      = Bitstream(6, int("000100", 2))
    CFG_IN       = Bitstream(6, int("000101", 2))
    INTEST       = Bitstream(6, int("000111", 2))
    USERCODE     = Bitstream(6, int("001000", 2))
    IDCODE       = Bitstream(6, int("001001", 2))
    HIGHZ        = Bitstream(6, int("001010", 2))
    JPROGRAM     = Bitstream(6, int("001011", 2))
    JSTART       = Bitstream(6, int("001100", 2))
    JSHUTDOWN    = Bitstream(6, int("001101", 2))
    ISC_ENABLE   = Bitstream(6, int("010000", 2))
    ISC_PROGRAM  = Bitstream(6, int("010001", 2))
    ISC_NOOP     = Bitstream(6, int("010100", 2))
    ISC_READ     = Bitstream(6, int("010101", 2))
    ISC_DISABLE  = Bitstream(6, int("010110", 2))
    ISC_DNA      = Bitstream(6, int("110001", 2))
    BYPASS       = Bitstream(6, int("111111", 2))

    def __init__(self):
        buses = usb.busses()
        xula = None
        for bus in buses:
            for device in bus.devices:
                if device.idVendor == 0x04d8 and device.idProduct == 0xff8c:
                    xula = device
        if xula is None:
            print "No XuLA device found on USB bus"
            sys.exit(1)

        print "Found XuLA on USB bus"

        self.handle = xula.open()

        if sys.platform != "win32":
		    # Don't detach under Windows because it will fail when using libusb-win32.
            try:
                self.handle.detachKernelDriver(0)
            except usb.USBError, error:
                # print "detachKernelDriver exception", error
                pass
        self.handle.claimInterface(0)

        def powercycle():
            m = bytes(RESET_CMD) + (chr(0) * 31)
            self.handle.bulkWrite(usb.ENDPOINT_OUT + 1, m, 1000)
            time.sleep(4)

        self.handle.resetEndpoint(usb.ENDPOINT_OUT + 1)
        self.handle.resetEndpoint(usb.ENDPOINT_IN + 1)
        #self.handle.reset()
        m = bytes(INFO_CMD, 0)
        self.handle.bulkWrite(usb.ENDPOINT_OUT + 1, m, 1000)
        device_info = None
        try:
            device_info = self.handle.bulkRead(usb.ENDPOINT_IN + 1, 32, 1000)
        except usb.USBError, error:
            powercycle()
        if device_info is None:
            try:
                device_info = self.handle.bulkRead(usb.ENDPOINT_IN + 1, 32, 1000)
            except usb.USBError, error:
                print 'USB I/O error'
                sys.exit(1)

        if (sum(device_info)) & 0xff != 0:
            print 'Device info Checksum error'
            sys.exit(1)

        print '  Product ID:  %02x %02x' % (device_info[1], device_info[2])
        print '  Version:     %d.%d' % (device_info[3], device_info[4])
        # Desc is 0-terminated string
        desc = device_info[5:-1]
        desclen = desc.index(0)
        print '  Description:', bytes(*desc[:desclen])

    # Sample TDO, output TMS and TDI values, pulse TCK, and return TDO value.
    def tick(self, tms, tdi):
        mask = 0
        if tms:
            mask |= 0x01
        if tdi:
            mask |= 0x02
        m = bytes(TMS_TDI_TDO_CMD, mask) # + (chr(0) * 30)
        self.handle.bulkWrite(usb.ENDPOINT_OUT + 1, m, 1000)
        r = self.handle.bulkRead(usb.ENDPOINT_IN + 1, 2, 1000)
        return (r[1] & 0x04) != 0;

    def bulktdi(self, bs):
        m = struct.pack("<BI", TDI_CMD, len(bs))
        self.handle.bulkWrite(usb.ENDPOINT_OUT + 1, m, 1000)
        t = time.time()
        if 0:
            b256 = bs # ([0] * (ps*8 - len(bs))) + list(bs)
            w256 = [(b << (i & 7)) for (i, b) in enumerate(b256)]
            m = array.array('B', [sum(w256[i:i+8]) for i in range(0, len(w256), 8)]).tostring()
        else:
            m = array.array('B', bs.tostring())
            m = array.array('B', [reverse_bits[c] for c in m.tolist()]).tostring()
        # print "(Bulk %d)" % len(m), ["%02x" % ord(c) for c in m[:50]]
        # print ["%02x" % ord(x) for x in m]

        self.handle.bulkWrite(usb.ENDPOINT_OUT + 1, m, 1000)
        self.debug_tms(1)
        if self.verbose:
            print "took", elapsed(time.time() - t)

    def word(self, bs):
        m = struct.pack("<BI", TDI_TDO_CMD, len(bs))
        self.handle.bulkWrite(usb.ENDPOINT_OUT + 1, m, 1000)
        b256 = bs # ([0] * (ps*8 - len(bs))) + list(bs)
        w256 = [(b << (i & 7)) for (i, b) in enumerate(b256)]
        m = array.array('B', [sum(w256[i:i+8]) for i in range(0, len(w256), 8)]).tostring()

        self.handle.bulkWrite(usb.ENDPOINT_OUT + 1, m, 1000)
        self.debug_tms(1)
        recv = self.handle.bulkRead(usb.ENDPOINT_IN + 1, 32, 1000)
        return recv[0]

    def bulktms(self, bs):
        GET_TDO_MASK = 0x01                       # Set if gathering TDO bits.
        PUT_TMS_MASK = 0x02                       # Set if TMS bits are included in the packets.
        TMS_VAL_MASK = 0x04                       # Static value for TMS if PUT_TMS_MASK is cleared.
        PUT_TDI_MASK = 0x08                       # Set if TDI bits are included in the packets.
        TDI_VAL_MASK = 0x10                       # Static value for TDI if PUT_TDI_MASK is cleared.
        DO_MULTIPLE_PACKETS_MASK = 0x80           # Set if command extends over multiple USB packets.
        m = struct.pack("<BIB", TAP_SEQ_CMD, len(bs) * 2, PUT_TDI_MASK | PUT_TMS_MASK)
        b256 = bs # ([0] * (ps*8 - len(bs))) + list(bs)
        w256 = [(b << (i & 7)) for (i, b) in enumerate(b256)]
        d = array.array('B', [sum(w256[i:i+8]) for i in range(0, len(w256), 8)]).tostring()

        # cmd, len, flags, tms, tdi
        m += d[0] + chr(0)
        print repr(m)
        self.handle.bulkWrite(usb.ENDPOINT_OUT + 1, m, 1000)
        for g in bs:
            self.debug_tms(g)

    def querychain(self):
        if 0:
            # do not need to count devices, because there is only one
            self.go_states(1,1,1,1,1)
            self.go_states(0,1,1,0,0)
            self.assert_state("Shift-IR")
            self.send_str("1" * 1000, 1)
            self.assert_state("Exit1-IR")
            self.go_states(1,1,0,0)
            self.send_str("0" * 1000, 0)
            ndevices = 0
            while self.do_bit(0, 1) == 0:
                ndevices += 1
        else:
            ndevices = 1

        self.go_states(1,1,1,1,1)
        self.go_states(0,1,0,0)

        return [self.do_nbit_cycle(32, 0) for i in range(ndevices)]

    def progpin(self, v):
        m = bytes(PROG_CMD, v) # + (chr(0) * 30)
        self.handle.bulkWrite(usb.ENDPOINT_OUT + 1, m, 1000)

    def flashpin(self, v):
        m = bytes(FLASH_ONOFF_CMD, v) # + (chr(0) * 30)
        self.handle.bulkWrite(usb.ENDPOINT_OUT + 1, m, 1000)
        self.handle.bulkRead(usb.ENDPOINT_IN + 1, 2, 2000)
        return

    def idcode(self):
        return self.LoadBSIRthenBSDR(self.IDCODE, Bitstream(32, 0), receive = True)

    def usercode(self):
        return self.LoadBSIRthenBSDR(self.USERCODE, Bitstream(32, 0), receive = True)

    def pulseTCK(self, c):
        self.assert_state("Run-Test/Idle")
        #for i in range(c):
        #    self.do_bit(0, 0)
        #return
        self.do_bit(0,0)
        c = c - 1
        m = bytes(RUNTEST_CMD, c & 0xff, (c >> 8) & 0xff, (c >> 16) & 0xff, (c >> 24) & 0xff)
        self.handle.bulkWrite(usb.ENDPOINT_OUT + 1, m, 1000)
        self.handle.bulkRead(usb.ENDPOINT_IN + 1, 5, 2000)
        return

    def DNA(self):
        self.tlr()
        self.LoadBSIRthenBSDR(self.JPROGRAM, None)
        time.sleep(.5)
        print "ISC_ENABLE", self.LoadBSIRthenBSDR(self.ISC_ENABLE, Bitstream(5, 0), receive = True)
        dna = self.LoadBSIRthenBSDR(self.ISC_DNA, Bitstream(57, 0), receive = True)
        print "ISC_DNA", hex(dna)
        return dna

    def ccl(self, rw, reg, cnt):
        """
        Return the 16-bit hex string for a Configuration
        Control Logic operation, (ug332 page 323).
        """
        assert rw in "rw"
        assert (0 <= reg < 64)
        assert (0 <= cnt < 32)
        m = 1 << 13     # Type 1 packet
        if rw == "r":
            m |= (1 << 11)
        else:
            m |= (2 << 11)
        m |= reg << 5
        m |= cnt
        return "%04x" % m

    def rdccl(self, reg):
        read_status = [
            "aa99",
            "2000",
            self.ccl('r', reg, 1),
            "2000",
            "2000",
        ]
        commands = "".join(read_status)
        self.LoadBSIRthenBSDR(self.CFG_IN, BitstreamHex(commands))
        return self.LoadBSIRthenBSDR(self.CFG_OUT, Bitstream(32, 0), receive = True)

    def resetcrc(self):
        print 'CRC=', hex(self.rdccl(0))

        write_crc = [
            "aa99",
            "2000",
            self.ccl('w', 5, 1),
            "0007",
            "2000",
        ]
        commands = "".join(write_crc)
        print commands
        self.LoadBSIRthenBSDR(self.CFG_IN, BitstreamHex(commands))
        print self.LoadBSIRthenBSDR(self.CFG_OUT, Bitstream(32, 0), receive = True)
        print 'CRC=', hex(self.rdccl(0))

    # see ug332, page 340
    def status(self):
        # packet format see ug332, page 323
        read_status = [
            "aa99",
            "2000",
            self.ccl('r', 8, 1),
            "2000",
            "2000",
        ]
        commands = "".join(read_status)
        self.LoadBSIRthenBSDR(self.CFG_IN, BitstreamHex(commands))
        status = self.LoadBSIRthenBSDR(self.CFG_OUT, Bitstream(32, 0), receive = True)

        print "status = %04x" % status
        vv = [
            ('SYNC_TIMEOUT',    1 & (status >> 15)),
            ('SEU_ERR',         1 & (status >> 14)),
            ('DONE',            1 & (status >> 13)),
            ('INIT',            1 & (status >> 12)),
            ('MODE',            7 & (status >> 9)),
            ('VSEL',            7 & (status >> 6)),
            ('GHIGH_B',         1 & (status >> 5)),
            ('GWE',             1 & (status >> 4)),
            ('GTS_CFG_B',       1 & (status >> 3)),
            ('DCM_LOCK',        1 & (status >> 2)),
            ('ID_ERROR',        1 & (status >> 1)),
            ('CRC_ERROR',       1 & (status >> 0))]
        for nm,v in vv:
            print "%16s %d" % (nm, v)

        return status

    # xapp139 - 
    # http://www.xilinx.com/support/documentation/application_notes/xapp452.pdf
    def load(self, bs):
        # Must follow JPROGRAM with CFG_IN to keep device locked to JTAG.
        # See AR 16829.
        self.LoadBSIRthenBSDR(self.JPROGRAM, None)
        self.LoadBSIRthenBSDR(self.CFG_IN, None)
        # print list(bs)[256:512]
        time.sleep(0.001)
        self.LoadBSIRthenBSDR(self.CFG_IN, bs)
        # BEFORE: (wants CCLK as startup clock)
        #self.tlr()
        #self.LoadBSIRthenBSDR(self.JSTART, None)
        # NOW: (works OK with JTAG Clock as startup clock)
        self.LoadBSIRthenBSDR(self.JSTART, None)
        self.pulseTCK(12)
        self.LoadBSIRthenBSDR(self.JSTART, Bitstream(22, 0))
        self.tlr()
        return True
        
    def load2(self, bs):
        self.LoadBSIRthenBSDR(self.JPROGRAM, None)
        self.pulseTCK(10000)
        self.LoadBSIRthenBSDR(self.CFG_IN, Bitstream(192, 0x0000000000000000e00000008001000c66aa9955ffffffff))
        self.LoadBSIRthenBSDR(self.JSHUTDOWN, None)
        self.pulseTCK(12)
        self.tlr()
        self.LoadBSIRthenBSDR(self.CFG_IN, Bitstream(96, 0x000000000000000066aa9955))
        self.LoadBSIRthenBSDR(self.CFG_IN, bs)
        for j in range(2):
            for i in range(2):
                self.tlr()
                self.go_state(0)
                self.assert_state("Run-Test/Idle");
            self.LoadBSIRthenBSDR(self.JSTART, None)
            self.pulseTCK(12)
            self.LoadBSIRthenBSDR(self.BYPASS, None)
            self.LoadBSIRthenBSDR(self.BYPASS, None)
        self.tlr()
        self.go_state(0)
        self.assert_state("Run-Test/Idle")
        return True

    # Added -- HP

    # check if the configuration supports a given capability.
    def has_capability(self, caps, bit_index):
        if (caps & 0xFF0000FF) == 0xA50000A5:  # upper and lower bytes must match this pattern
            if caps & (1 << bit_index):
                return True
        return False

    # load FPGA with flash programmer
    def configure(self, filename):
        # Download the configuration bitstream to the FPGA.
        self.progpin(1)
        self.progpin(0)
        self.progpin(1)
        time.sleep(0.03)
        t = time.time()
        status = self.load(BitFile(filename))
        t = time.time() - t
        if self.verbose:
            print "Time to download bitstream =", elapsed(t)
        return status

    # write bitstream to flash
    def write_flash(self, bs, loAddr, doStart):
    
        self.flashpin(1)  # release uC hold on Flash chip

        # download the USER instruction to the FPGA to enable the JTAG circuitry
        self.initTAP()
        self.assert_state("Shift-IR")
        self.sendbs(self.USER1)
        # go to the SHIFT-DR state where the Flash interface circuitry can be controlled
        self.go_states(1,1,0,0)  # -> UpdateIR -> SelectDRScan -> CaptureDR -> ShiftDR
        self.assert_state("Shift-DR")
        # download the instruction that gets the interface capabilities from the FPGA
        self.sendbs(INSTR_CAPABILITIES)
        # readback the capabilities of the interface
        self.go_states(0,1,0)    # -> PauseDR -> Exit2DR -> ShiftDR
        self.assert_state("Shift-DR")
        data = self.sendrecvbs(Bitstream(TDO_LENGTH, 0))
        # check the capabilities to see if Flash writes are supported
        flashIntfcAlreadyLoaded = self.has_capability(data, CAPABLE_FLASH_WRITE_BIT)

        # only download the Flash interface if this is the first download of data to the Flash.
        # otherwise the interface should already be in place.
        if doStart and not flashIntfcAlreadyLoaded:
            # configure the FPGA with the Flash interface circuit.
            print "Loading the FPGA with the Flash interface circuit"
            if not self.configure("fintf_jtag.bit"):
                print "Error downloading Flash interface circuit!!"
                return False
	    print

        # download the USER instruction to the FPGA to enable the JTAG circuitry
        # that will be used to access the Flash
        self.initTAP()
        self.assert_state("Shift-IR")
        self.sendbs(self.USER1)

        # go to the SHIFT-DR state where the Flash interface circuitry can be controlled
        self.go_states(1,1,0,0)
        self.assert_state("Shift-DR")

        # download the instruction that gets the Flash organization from the FPGA
        self.sendbs(INSTR_FLASH_SIZE)

        # readback the widths of the Flash address and data buses
        self.go_states(0,1,0)    # -> PauseDR -> Exit2DR -> ShiftDR
        self.assert_state("Shift-DR")
        data = self.sendrecvbs(Bitstream(24, 0))
        data = Bitstream(24, data)
        w256 = [(b << (i & 7)) for (i, b) in enumerate(data)]
        sizes = array.array('B', [sum(w256[i:i+8]) for i in range(0, len(w256), 8)]) # convert to byte array
        dataWidth = sizes[0]
        addrWidth = sizes[1]
        blockAddrWidth = sizes[2] # address width of the block RAM that holds data to be written to Flash
        blockSize = 1 << blockAddrWidth
        blockAddrMask = ~(blockSize - 1)

        # stride is the number of byte addresses that are contained in each Flash word address
        stride = dataWidth / 8  # stride is 1,2,4 for data bus width of 8, 16 or 32
        # address mask zeroes the lower bits of the byte address for alignment to the Flash word size
        addrMask = ~(stride - 1)

        if self.verbose:
            print "dataWidth =", dataWidth
            print "addrWidth =", addrWidth
            print "stride    =", stride
            print "addrMask  =", addrMask
            print "blockSize =", blockSize

        if doStart:
            # erase the flash chip
            print "Erasing Flash",
            sys.stdout.flush()
            self.go_states(0,1,0)  # -> PauseDR -> Exit2DR -> ShiftDR
            self.assert_state("Shift-DR")
            self.sendbs(INSTR_FLASH_ERASE)
            while True:
                self.go_states(0,1,0)  # -> PauseDR -> Exit2DR -> ShiftDR
                self.assert_state("Shift-DR")
                data = self.sendrecvbs(Bitstream(TDO_LENGTH, 0))
                if self.verbose:
                    print "erase result = 0x%08x" % data
                time.sleep(0.5)
                # simple progress indicator
                print ".",
                sys.stdout.flush()
                if data == OP_INPROGRESS:
                    continue
                if data == OP_FAILED:
                    print "Flash erase failed!!"
                    return False
                break
            print

        # download to Flash
        print "Downloading data",
        sys.stdout.flush()

        address = loAddr  # start byte address
        count   = 0       # count of bytes written

        # load the whole file into a byte string for easier access
        #bits = bs.tostring()
        m = array.array('B', bs.tostring())
        bits = array.array('B', [reverse_bits[c] for c in m.tolist()]).tostring()

        while count < len(bits):

            # fill buffer with next block from file
            buf = bits[count:count+blockSize]

            numBytes = len(buf)

            if numBytes % stride:
                # better pad the buffer with a few 0xFF bytes and proceed anyway...
                print "Cannot download an odd number of bytes to multibyte-wide Flash!"
                return False

            if address & ~addrMask:
                print "Cannot download to multibyte-wide Flash using an odd byte-starting address!"
                return False

            # download the buffer
            if self.verbose:
                print "address  = 0x%08x" % address
                print "numBytes =", numBytes

            # store the number of words that will be downloaded to Flash into the download instruction operands
            numWords = numBytes / stride
            cnt = Bitstream(addrWidth, numWords)

            # adjust the byte starting address for the Flash word size
            wordAddr = address / stride
            # partition the word address into bytes and store in the operand storage area
            addr = Bitstream(addrWidth, wordAddr)

            # send the Flash download instruction and the Flash address and download length
            ##payload = cnt + addr + INSTR_FLASH_PGM
            self.go_states(0,1,0)  # -> PauseDR -> Exit2DR -> ShiftDR
            self.assert_state("Shift-DR")
            ##self.sendrecvbs(payload)
            #self.sendbs(INSTR_FLASH_PGM)
            #self.go_states(0,1,0)  # -> PauseDR -> Exit2DR -> ShiftDR
            #self.assert_state("Shift-DR")
            #self.sendbs(addr)
            #self.go_states(0,1,0)  # -> PauseDR -> Exit2DR -> ShiftDR
            #self.assert_state("Shift-DR")
            #self.sendbs(cnt)
            for d in INSTR_FLASH_PGM:
                self.do_bit(tms = 0, tdi = d)
            for d in addr:
                self.do_bit(tms = 0, tdi = d)
            for (is_lastbit, d) in islast(cnt):
                self.do_bit(tms = is_lastbit, tdi = d)

            # now download the data words to block RAM
            data = BitstreamString(buf)  # len = 8 * numBytes
            self.go_states(0,1,0)  # -> PauseDR -> Exit2DR -> ShiftDR
            self.assert_state("Shift-DR")
            t = time.time()
            self.sendbs(data)
            t = time.time() - t
            if self.verbose:
                print "Time to download", 8 * numBytes, "bits =", elapsed(t)
                print "Transfer rate =", 8 * numBytes / t, "bps"

            # wait until the block RAM contents are programmed into the Flash
            while True:
                self.go_states(0,1,0)  # -> PauseDR -> Exit2DR -> ShiftDR
                self.assert_state("Shift-DR")
                data = self.sendrecvbs(Bitstream(TDO_LENGTH, 0))
                if self.verbose:
                    print "block write result = 0x%08x" % data
                if data == OP_INPROGRESS:
                    continue
                if data == OP_FAILED:
                    print "Download failed!!"
                    return False
                break

            # simple progress bar
            print ".",
            sys.stdout.flush()

            # compute the address for the next block
            address += numBytes
            count   += numBytes

        print
        
        self.flashpin(0)

        return True

    def read_flash(self, filename, loAddr, hiAddr, doStart):

        self.flashpin(1)  # release uC hold on flash chip

        # create the output file
        outf = open(filename, "wb")

        # download the USER instruction to the FPGA to enable the JTAG circuitry
        self.initTAP()
        self.assert_state("Shift-IR")
        self.sendbs(self.USER1)
        # go to the SHIFT-DR state where the Flash interface circuitry can be controlled
        self.go_states(1,1,0,0) # -> UpdateIR -> SelectDRScan -> CaptureDR -> ShiftDR
        self.assert_state("Shift-DR")
        # download the instruction that gets the interface capabilities from the FPGA
        self.sendbs(INSTR_CAPABILITIES)
        # readback the capabilities of the interface
        self.go_states(0,1,0) # -> PauseDR -> Exit2DR -> ShiftDR
        data = self.sendrecvbs(Bitstream(TDO_LENGTH, 0))
        # check the capabilities to see if Flash reads are supported
        flashIntfcAlreadyLoaded = self.has_capability(data, CAPABLE_FLASH_READ_BIT)

        if self.verbose:
            print "CAPABILITIES = 0x%08x" % data

        # only download the Flash interface if this is the first upload of data from the Flash.
        # Otherwise the interface should already be in place.
        if doStart and not flashIntfcAlreadyLoaded:
            # configure the FPGA with the Flash interface circuit.
            print "Loading the FPGA with the Flash interface circuit"
            if not self.configure("fintf_jtag.bit"):
                print "Error configuring FPGA with Flash programming circuit!"
                return False

        # download the USER instruction to the FPGA to enable the JTAG circuitry
        # that will be used to access the Flash
        self.initTAP()
        self.assert_state("Shift-IR")
        self.sendbs(self.USER1)

        # go to the SHIFT-DR state where the Flash interface circuitry can be controlled
        self.go_states(1,1,0,0) # -> UpdateIR -> SelectDRScan -> CaptureDR -> ShiftDR
        self.assert_state("Shift-DR")

        # download the instruction that gets the Flash organization from the FPGA
        self.sendbs(INSTR_FLASH_SIZE)

        # readback the widths of the Flash address and data buses
        self.go_states(0,1,0)  # -> PauseDR -> Exit2DR -> ShiftDR
        self.assert_state("Shift-DR")
        data = self.sendrecvbs(Bitstream(24, 0))
        data = Bitstream(24, data)
        w256 = [(b << (i & 7)) for (i, b) in enumerate(data)]
        sizes = array.array('B', [sum(w256[i:i+8]) for i in range(0, len(w256), 8)])
        dataWidth = sizes[0]
        addrWidth = sizes[1]
        blockAddrWidth = sizes[2] # address width of the block RAM that holds data to be written to Flash

        # stride is the number of byte addresses that are contained in each Flash word address
        stride = dataWidth / 8    # stride is 1,2,4 for data bus width of 8, 16 or 32
        # address mask zeroes the lower bits of the byte address for alignment to the Flash word size
        addrMask = ~(stride - 1)

        if self.verbose:
            print "dataWidth      =", dataWidth
            print "addrWidth      =", addrWidth
            print "stride         =", stride
            print "addrMask       =", addrMask
            print "blockAddrWidth =", blockAddrWidth

        # check address and length of the upload byte address range to make sure it aligns with Flash word size
        if (hiAddr-loAddr+1) % stride:
            print "Cannot upload an odd number of bytes from multibyte-wide Flash!"
            return False
        if loAddr & ~addrMask:
            print "Cannot upload from multibyte-wide Flash using an odd byte-starting address!"
            return False

        print "Reading Flash contents into", filename

        # read blocks Flash and save them into the output file
        wordAddr = loAddr / stride        # address of word in Flash
        numBytes = hiAddr - loAddr + 1    # number of bytes to upload to the hex file
        numWords = numBytes / stride      # number of Flash words to upload

        if self.verbose:
            print "wordAddr = 0x%08x" % wordAddr
            print "numBytes =", numBytes
            print "numWords =", numWords

        # partition the word address into bytes and store in the operand storage area
        addr = Bitstream(addrWidth, wordAddr)
        # store the number of words that will be uploaded from Flash into the upload instruction operands
        cnt = Bitstream(addrWidth, numWords)

        # send the Flash upload instruction and the Flash address and upload length
        ##payload = cnt + addr + INSTR_FLASH_READ
        self.go_states(0,1,0)  # -> PauseDR -> Exit2DR -> ShiftDR
        self.assert_state("Shift-DR")
        ##self.sendrecvbs(payload)
        for d in INSTR_FLASH_READ:
            self.do_bit(tms = 0, tdi = d)
        for d in addr:
            self.do_bit(tms = 0, tdi = d)
        for (is_lastbit, d) in islast(cnt):
            self.do_bit(tms = is_lastbit, tdi = d)

        # now upload the data words from Flash
        self.go_states(0,1,0)  # -> PauseDR -> Exit2DR -> ShiftDR
        self.assert_state("Shift-DR")
        t = time.time()
        data = self.sendrecvbs(Bitstream(8 * numBytes, 0))
        t = time.time() - t
        if self.verbose:
            print "Time to upload", 8 * numBytes, "bits =", elapsed(t)
            print "Transfer rate =", 8 * numBytes / t, "bps"

        # convert uploaded data from bitstream into a byte string
        data = Bitstream(8 * numBytes, data)
        w256 = [(b << (i & 7)) for (i, b) in enumerate(data)]
        databytes = array.array('B', [sum(w256[i:i+8]) for i in range(0, len(w256), 8)]) #.tostring()

        outf.write(databytes)
        outf.close()  # close-up the output file
        
        self.flashpin(0)

        return True

    # Added -- HP
    def hostio(self, id, payload, resplen, recv = False):
        if self.state() != "Shift-IR":
            self.rti()
            self.go_states(1,1,0,0)
        self.assert_state("Shift-IR")
        self.sendbs(self.USER1)
        self.go_states(1,1,0,0)
        self.assert_state("Shift-DR")
        self.do_nbit_cycle(8, id)
        self.do_nbit_cycle(32, len(payload) + resplen) # number of payload bits
        for d in payload:
            self.do_bit(tms = 0, tdi = d)
        r = None
        if recv:
            r = self.sendrecvbs(Bitstream(16, 0))
        self.go_state(1)
        self.assert_state("Update-DR")
        self.go_state(0)
        self.assert_state("Run-Test/Idle")
        return r
    
    def memquery(self, id):
        return self.hostio(id, Bitstream(2, int("01", 2)), 16, recv = True)

    def memread(self, id, addr, ndata):
        return self.hostio(id, Bitstream(34, 0x300000000 + addr), ndata, recv = True)

    def memwrite(self, id, addr, data):
        # TODO
        return

    def dutquery(self, id):
        return self.hostio(id, Bitstream(2, int("01", 2)), 16, recv = True)

    def dutread(self, id, nvalues):
        return self.hostio(id, Bitstream(34, 0x300000000 + nvalues), nvalues, recv = True)

    def dutwrite(self, id, values):
        # TODO
        return

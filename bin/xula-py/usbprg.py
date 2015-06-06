#! /usr/bin/env python

from argparse import ArgumentParser
from collections import namedtuple
from xs import eeprom
from xs import usbcmds
from xs.hex import HexRecord
from xs.util import based_int
from xs.util import usbSim

import logging
import numpy
import os
import time
import usb.core
import usb.util

Defines = namedtuple ("Defines", ["FLASH_ADDR_BOT",
                                  "FLASH_ADDR_TOP",
                                  "VERSION"])
define = Defines (0x0800, 0x6000, "1.2.1")


def _connect (idVendor, idProduct, use_sim):
    dev = usbSim() if use_sim else usb.core.find (idVendor=idVendor,
                                                  idProduct=idProduct)
    return dev

def _erase (dev, do_work,
                 bot=define.FLASH_ADDR_BOT, top=define.FLASH_ADDR_TOP):
    success = do_work
    bot &= 0xff00
    top = top if (top & 0xff) == 0 else ((top & 0xff00) + 0x100)
    
    if do_work:
        logging.info ("Erasing the flash.")
        logging.info ("   Starting address: " + hex (bot))
        logging.info ("   Ending address:   " + hex (top))
        tx = numpy.empty ((5,), dtype=numpy.uint8)
        block_count =  1
        block_size  = 64
        for addr in xrange (bot, top, block_size*block_count):
            # from xsusbprg.cpp v 5.1.3:
            #    Flash doesn't erase if # blocks is larger than 16.
            #    Don't know why.  Set to 1 to be sure.
            tx[0] = numpy.uint8(usbcmds.enum.ERASE_FLASH_CMD)
            tx[1] = numpy.uint8(block_count)
            tx[2] = numpy.uint8( addr      & 0xff)
            tx[3] = numpy.uint8((addr>>8)  & 0xff)
            tx[4] = numpy.uint8((addr>>16) & 0xff)
            txlen = dev.write (1, tx, 0, 100)
            rx = dev.read (0x81, 1, 0, 100)

            if len (rx) != 1 and txlen != tx.size:
                logging.info ("Erasing block starting at address " + hex(addr))
                logging.error ("Did not successfully erase the EEPROM.")
                success = False
                break
            pass

        logging.info (("Successfully erased" if success else "Failed to erase")
                      + " the flash.")
        pass
    return success

def _program (dev, fn, usb_info, do_work):
    success = do_work
    if do_work:
        logging.info ("Programming the USB device.")
        hx = HexRecord(fn, ignore_below=0x100)
        logging.info ("Minimum program address is " + hex (hx.min_addr()) +
                      " and boundary is at " + hex (define.FLASH_ADDR_BOT))
        logging.info ("Maximum program address is " + hex (hx.max_addr()) +
                      " and boundary is at " + hex (define.FLASH_ADDR_TOP))
        success = define.FLASH_ADDR_BOT <= hx.min_addr() and \
                  hx.max_addr() < define.FLASH_ADDR_TOP
        
        if not success:
            logging.error ("Program file outside of address bounds.")
            return
        
        logging.info ("Set the hardware for a reflash.")
        success = eeprom.write (dev,
                                eeprom.define.BOOT_SELECT_FLAG_ADDR,
                                eeprom.define.BOOT_INTO_REFLASH_MODE)
        if success:
            logging.info ("Bring the hardware back in reflash mode.")
            _reset (dev)
            usb.util.dispose_resources (dev)
            time.sleep (2)
            dev = _connect (**usb_info)
            success &= dev is not None
            
            if success:
                success &= _erase  (dev, success,
                                    hx.min_addr(), hx.max_addr())
                success &= _write  (dev, hx, success)
                success &= _verify (dev, hx, success)
                
                if success:
                    logging.info ("Bring the hardware back in user mode.")
                    eeprom.write (dev,
                                  eeprom.define.BOOT_SELECT_FLAG_ADDR,
                                  eeprom.define.BOOT_INTO_USER_MODE)
                    _reset (dev)
                    usb.util.dispose_resources (dev)
                    pass
                
                logging.info (("Successfully programmed" if success else
                               "Failed to program") + " the device.")
                pass
            else: logging.info ("Cannot reconnect to the hardware.")
            pass
        else: logging.info ("Could not set the EEPROM to a reflash state.")
        pass
    return success
    
def _reset (dev):
    logging.info ("Blindly resetting the device.")
    tx = numpy.empty ((64,), dtype=numpy.uint8)
    tx[0] = numpy.uint8(usbcmds.enum.RESET_CMD)
    dev.write (1, tx, 0, 100)
    logging.info ("Device has been told to reset.")
    return

__hexdict = { 0:'0',1:'1',2:'2',3:'3',4:'4',5:'5',6:'6',7:'7',8:'8',9:'9',
              10:'a',11:'b',12:'c',13:'d',14:'e',15:'f' }
def _verify (dev, hx, do_work):
    def tohex (n):
        ln = n & 0xf
        hn = (n >> 4) & 0xf
        return "0x" + __hexdict[hn] + __hexdict[ln]
    
    success = do_work
    
    if do_work:
        logging.info ("Verifying the flash program.")
        tx = numpy.empty ((5,), dtype=numpy.uint8)
        for addr, data in hx.iterate():
            tx[0] = numpy.uint8 (usbcmds.enum.READ_FLASH_CMD)
            tx[1] = numpy.uint8 (16)
            tx[2] = numpy.uint8 ( addr        & 0xf0) # 16 byte align address
            tx[3] = numpy.uint8 ((addr >> 8)  & 0xff)
            tx[4] = numpy.uint8 ((addr >> 16) & 0xff)
            sent = dev.write (1, tx, 0, 100)
            rx = dev.read (0x81, 21, 0, 100)
            
            if sent != tx.size or len (rx) != 21:
                logging.info ("Attempting to read at address block: " +
                              hex (addr & 0xfff0))
                logging.info ("Data sent was " + str (sent) + " bytes but "
                              "expected to send " + str (data.size) + " bytes.")
                logging.info ("Data requested was " + str (data.size + 5) +
                              " bytes but only " + str (rx.size) +
                              " bytes were received.")
                logging.error ("Could not send the entire record.")
                break

            match = True
            for i in xrange (data.size):
                match &= data[i] == rx[i + (addr & 0xf) + 5]
                pass

            if not match:
                success = False
                logging.info ("Verification at address block " +
                              hex (addr & 0xfff0) + " failed.")
                sdata = ""
                for d in data: sdata += tohex (d) + " "
                logging.info ("   Expectation: " + sdata)
                sdata = ""
                for d in rx[(addr & 0xf) + 5:(addr & 0xf) + 5 + len(data)]:
                    sdata += tohex (d) + " "
                    pass
                logging.info ("   Actual:      " + sdata)
                pass
            pass
        logging.info (("Successfully verified" if success else
                       "Failed to verify") + " the program on the flash.")
        pass
    return success

def _write (dev, hx, do_work):
    success = do_work
    
    if do_work:
        logging.info ("Writing the program to flash.")
        tx = numpy.empty ((22,), dtype=numpy.uint8)
        ignore = numpy.ones((16,), dtype=numpy.uint8)*255
        for addr, data in hx.iterate():
            tx[0] = numpy.uint8 (usbcmds.enum.WRITE_FLASH_CMD)
            tx[1] = numpy.uint8 (16)
            tx[2] = numpy.uint8 ( addr        & 0xf0) # 16 byte align address
            tx[3] = numpy.uint8 ((addr >> 8)  & 0xff)
            tx[4] = numpy.uint8 ((addr >> 16) & 0xff)
            tx[5:21] = ignore # set them to 0xff so that the eeprom ignore them
            tx[(addr & 0xf) + 5:(addr & 0xf) + data.size + 5] = data
            sent = dev.write (1, tx, 0, 100)
            dev.read (0x81, 1, 0, 100) # sends the command ID back
            
            if sent != tx.size:
                success = False
                logging.info ("Attempting to write at address block: " +
                              hex (addr & 0xfff0))
                logging.info ("Data sent was " + str (sent) + " bytes but "
                              "expected to send " + str (data.size) + " bytes.")
                logging.error ("Could not send the entire record.")
                break
            pass
        logging.info (("Successfully wrote" if success else "Failed to write")
                      + " the program to flash.")
        pass
    return success

if __name__ == "__main__":
    p = ArgumentParser(description="Reprogram an XS device with a PIC18 family microchip via the USB. The single input is the .hex file generated from MPLAB or MPLAB-X. It then uses the information to burn the program into the EEPROM and then reset the device. It will limit the writing to be between " + hex (define.FLASH_ADDR_BOT) + ".." + hex (define.FLASH_ADDR_TOP) + " inclusive.")
    p.add_argument ("-f", "--file-name", type=str, required=True,
                    help="The name of the file to fill during a read or empty during a write.")
    p.add_argument ("-l", "--log-file", type=str, default="./xsusbprg.log",
                    help="Name of the log file to fill with all the nasty output for debugging and tracing what this program is doing: [%(default)s]")
    p.add_argument ("-s", "--simulator", action="store_true", default=False,
                    help="Use a usb simulator instead of an actual device.")
    p.add_argument ("-u", "--usb-vid", type=based_int, default=0x04d8,
                    help="The vendor ID of the usb device to access: [%(default)s]")
    p.add_argument ("-p", "--usb-pid", type=based_int, default=0xff8c,
                    help="The product ID of the usb device to access: [%(default)s]")
    p.add_argument ("-v", "--version",
                    action='version', version="%(prog)s " + define.VERSION,
                    help="Print the version number of this program and exit.")
    args = p.parse_args()
    usb_info = {'idVendor':args.usb_vid,
                'idProduct':args.usb_pid,
                'use_sim':args.simulator}
    logging.basicConfig (filemode='w',
                         filename=args.log_file,
                         format="%(levelname)s:%(message)s",
                         level=logging.INFO)
    logging.info ("Command line arguments are parsed.")
    dev = _connect (**usb_info)
    success = True
    
    if dev is None:
        success = False
        logging.error ("Could not find the USB device with vendor id " +
                       hex (args.usb_vid) + " and product id " +
                       hex (args.usb_pid))
        pass

    if not os.path.exists (args.file_name) or \
           os.path.getsize (args.file_name) == 0:
        success = False
        logging.error ("Either the file " + args.file_name + " does not exist "+
                       "or it is of zero length.")
        pass
    
    success = _program (dev, args.file_name, usb_info, success)
    print "EEPROM access as " + ("successful" if success else "unsuccessful") +\
          " see the logfile (" + args.log_file + ") for details."
    pass


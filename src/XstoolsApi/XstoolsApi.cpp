/***********************************************************************************
 *   This program is free software; you can redistribute it and/or
 *   modify it under the terms of the GNU General Public License
 *   as published by the Free Software Foundation; either version 2
 *   of the License, or (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License
 *   along with this program; if not, write to the Free Software
 *   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
 *   02111-1307, USA.
 *
 *   ©2011 - X Engineering Software Systems Corp. (www.xess.com)
 ***********************************************************************************/



/***********************************************************************************
 *  (Place description of file contents here.)
 ***********************************************************************************/


#include "stdafx.h"
#include <iostream>
#include <string>
#include "XstoolsLib.h"
#include "XstoolsApi.h"


/// Open a channel to a HostIoToMemory module in the FPGA.
///\return A pointer to the channel.
extern "C" XSTOOLSAPI HostIoToMemory *XsMemInit(
    unsigned int xsusbInst,   ///< [in] XSUSB port instance (usually 0).
    unsigned int moduleId,    ///< [in] HostIo module identifier.
    unsigned int &rAddrWidth, ///< [out] Number of address bits.
    unsigned int &rDataWidth  ///< [out] Number of data bits.
    )
{
    unsigned int vid               = 0x04D8; // XSUSB vendor ID.
    unsigned int pid               = 0xFF8C; // XSUSB product ID.
    unsigned int endpoint          = 1;      // XSUSB endpoint.

    // Create an object for USB communication.
    LibusbPort *port_ptr           = new LibusbPort( vid, pid, xsusbInst, endpoint );

    // Open the USB object for bidirectional communication.
    XsError error                  = port_ptr->Open();
    if ( error.IsError() )
        return NULL;  // Return NULL if communication is not possible.

    // Create an object for doing JTAG operations over the USB link.
    JtagPort *jtag_ptr             = new JtagPort( port_ptr );

    // Create an object for doing I/O with memory-like circuitry in the FPGA over the JTAG link.
    HostIoToMemory &host_io_module = *new HostIoToMemory( jtag_ptr );

    // Set the USER1 JTAG opcode that enables I/O operations with the FPGA circuitry.
    host_io_module.UserInstr() = BitBuffer( "000010" );

    // Reset the I/O object to start it running.
    host_io_module.Reset();

    // Get & store the sizes of the address and data buses of the memory circuitry.
    host_io_module.GetSize( moduleId, rAddrWidth, rDataWidth );

    if(rAddrWidth == 0 || rDataWidth == 0)
        return NULL; // Non-existent memory circuit! Return NULL pointer.

    // Return a pointer to the object for communicating with the memory circuit in the FPGA.
    return &host_io_module;
} // XsMemInit



/// Send data to memory-like module in FPGA.
///\return 0 if operation was successful, non-zero if failure.
extern "C" XSTOOLSAPI int XsMemWrite(
    HostIoToMemory           *pHostIoModule, ///< [in] Pointer to HostIoToMemory module.
    unsigned int const       addr,           ///< [in] Starting address for writing to memory.
    unsigned long long const *pData,         ///< [in] Pointer to data elements destined for memory.
    unsigned int const       nData           ///< [in] Number of data elements to write.
    )
{
    HostIoToMemory &host_io_module = *pHostIoModule;

    // Convert data array to queue so we can pass it.
    HostIoToMemory::MemoryDataQueue data;
    for ( unsigned int i = 0; i < nData; i++ )
        data.push_back( pData[i] );

    // Do write operation and record whatever errors occur.
    XsError error = host_io_module.Write( (HostIoToMemory::MemoryAddressType)addr, data );

    // Return 0 if no errors occurred, non-zero if errors did occur.
    return error.IsError() ? 1 : 0;
}



/// Get data from memory-like module in FPGA.
///\return 0 if operation was successful, non-zero if failure.
extern "C" XSTOOLSAPI int XsMemRead(
    HostIoToMemory            *pHostIoModule, ///< [in] Pointer to HostIoToMemory module.
    unsigned int const        addr,           ///< [in] Starting address for reading from memory.
    unsigned long long *const pData,          ///< [in] Pointer to storage for data elements from memory.
    unsigned int              nData           ///< [in] Number of data elements to read.
    )
{
    HostIoToMemory &host_io_module = *pHostIoModule;

    // Do read operation and record whatever errors occur.
    HostIoToMemory::MemoryDataQueue data;
    XsError error                  = host_io_module.Read( (HostIoToMemory::MemoryAddressType)addr,
                                                          (HostIoToMemory::MemoryAddressType)nData, data );

    // Return non-zero if any errors did occur.
    if ( error.IsError() )
        return 1;

    // Return non-zero if amount of data received is less than was requested.
    if ( data.size() != nData )
        return 2;

    // Move data from queue to array.
    for ( unsigned int i = 0; i < nData; i++ )
    {
        pData[i] = data.front();
        data.pop_front();
    }

    // Operation was successful.
    return 0;
}



/// Open a channel to a HostIoToDut module in the FPGA.
///\return A pointer to the channel.
extern "C" XSTOOLSAPI HostIoToDut *XsDutInit(
    unsigned int xsusbInst,   ///< [in] XSUSB port instance (usually 0).
    unsigned int moduleId,    ///< [in] HostIo module identifier.
    unsigned int &rNumInputs, ///<[out] Number of bits in input vector to DUT.
    unsigned int &rNumOutputs ///<[out] Number of bits in output vector of DUT.
    )
{
    unsigned int vid            = 0x04D8; // XSUSB vendor ID.
    unsigned int pid            = 0xFF8C; // XSUSB product ID.
    unsigned int endpoint       = 1;      // XSUSB endpoint.

    // Create an object for USB communication.
    LibusbPort *port_ptr        = new LibusbPort( vid, pid, xsusbInst, endpoint );

    // Open the USB object for bidirectional communication.
    XsError error               = port_ptr->Open();
    if ( error.IsError() )
        return NULL;  // Return NULL if communication is not possible.

    // Create an object for doing JTAG operations over the USB link.
    JtagPort *jtag_ptr          = new JtagPort( port_ptr );

    // Create an object for doing I/O with device-under-test (DUT) in the FPGA over the JTAG link.
    HostIoToDut &host_io_module = *new HostIoToDut( jtag_ptr );

    // Set the USER1 JTAG opcode that enables I/O operations with the FPGA circuitry.
    host_io_module.UserInstr() = BitBuffer( "000010" );

    // Reset the I/O object to start it running.
    host_io_module.Reset();

    // Get & store the sizes of input and output vectors of the DUT.
    host_io_module.GetSize( moduleId, rNumInputs, rNumOutputs );

    if(rNumInputs == 0 && rNumOutputs == 0)
        return NULL; // Non-existent DUT! Return NULL pointer.

    // Return a pointer to the object for communicating with the DUT in the FPGA.
    return &host_io_module;
} // XsDutInit



/// Send inputs to a DUT in the FPGA.
///\return 0 if operation was successful, non-zero if failure.
extern "C" XSTOOLSAPI int XsDutWrite(
    HostIoToDut                *pHostIoModule, ///< [in] Pointer to HostIoToDut module.
    unsigned char const *const pInputs,        ///< [in] Pointer to input vector values for DUT.
    unsigned int               numInputs       ///< [in] Number of inputs to force to given values.
    )
{
    HostIoToDut &host_io_module = *pHostIoModule;

    // Force bits onto DUT inputs and record whatever errors occur.
    XsError error               = host_io_module.Write( BitBuffer( pInputs, numInputs ) );

    // Return 0 if no errors occurred, non-zero if errors did occur.
    return error.IsError() ? 1 : 0;
}



/// Get outputs from a DUT in the FPGA.
///\return 0 if operation was successful, non-zero if failure.
extern "C" XSTOOLSAPI int XsDutRead(
    HostIoToDut          *pHostIoModule, ///< [in] Pointer to HostIoToDut module.
    unsigned char *const pOutputs,       ///< [in] Pointer to output vector values from DUT.
    unsigned int         numOutputs      ///< [in] Number of outputs to read from DUT.
    )
{
    HostIoToDut &host_io_module = *pHostIoModule;

    // Read outputs of DUT and record whatever errors occur.
    BitBuffer outputs;
    XsError error               = host_io_module.Read( outputs );

    // Return non-zero if any errors did occur.
    if ( error.IsError() )
        return 1;

    // Return non-zero if amount of data received is less than was requested.
    if ( outputs.size() != numOutputs )
        return 2;

    // Move data from bit queue into array.
    for ( unsigned int i = 0; i < numOutputs; i++ )
    {
        pOutputs[i] = outputs.front();
        outputs.pop_front();
    }

    // Operation was successful.
    return 0;
}

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
 * Object for performing memory-mapped I/O between the host PC and the FPGA board.
 ***********************************************************************************/

#include "HostIoToMemory.h"


/// The opcodes for the operations a memory device can perform.
BitBuffer const HostIoToMemory::NOP_OPCODE( "00" );   ///< No operation.
BitBuffer const HostIoToMemory::SIZE_OPCODE( "01" );  ///< Query address and data widths.
BitBuffer const HostIoToMemory::WRITE_OPCODE( "10" ); ///< Write to memory.
BitBuffer const HostIoToMemory::READ_OPCODE( "11" );  ///< Read from memory.

unsigned int const HostIoToMemory::SIZE_RESULT_LENGTH = 16; ///< Length of result from query operation.



/// Default constructor.
HostIoToMemory::HostIoToMemory( JtagPort *pJtagPort ) ///< Pointer to JTAG port of device.
    : HostIo( pJtagPort )
{
    Init();
}



/// Destructor.
HostIoToMemory::~HostIoToMemory( void )
{
}



/// Initialize memory parameters.
///\return An error object.
XsError HostIoToMemory::GetSize(
    unsigned int const id,             ///< Memory module identifier.
    unsigned int       &rAddressWidth, ///< Address width.
    unsigned int       &rDataWidth     ///< Data width.
    )
{
    XsError error;

    mId           = BitBuffer( id, ID_FIELD_LENGTH ); // Store id for this memory.

    // Query memory for its address and data widths.
    BitBuffer params;
    unsigned int const SKIP_CYCLES = 1;
    error        |= HostIoCmd( mId, SIZE_OPCODE, SIZE_RESULT_LENGTH + SKIP_CYCLES, params );
    params.pop_front( SKIP_CYCLES );
    mAddressWidth = params.front( SIZE_RESULT_LENGTH / 2 ); // First 16 bits contain the address width.
    rAddressWidth = mAddressWidth;
    params.pop_front( SIZE_RESULT_LENGTH / 2 );             // Get rid of the address width.
    mDataWidth    = params.front( SIZE_RESULT_LENGTH / 2 ); // Next 16 bits contain the data width.
    rDataWidth    = mDataWidth;
    mLastError    = error;
    return error;
}



/// Read value from memory device.
///\return An error object.
XsError HostIoToMemory::Read(
    MemoryAddressType const address,  ///< Address to read from memory.
    MemoryDataType          &rValue ) ///< Store value read from memory here.
{
    deque<unsigned long long> mem_vals;
    mLastError = Read( address, 1, mem_vals );
    rValue     = mem_vals.front();
    return mLastError;
}



/// Read multiple, sequential addresses from memory device.
///\return An error object.
XsError HostIoToMemory::Read(
    MemoryAddressType const address,   ///< Starting address for reading memory.
    MemoryAddressType const numValues, ///< Number of values to get from memory.
    MemoryDataQueue         &rValues ) ///< Queue for storing values.
{
    assert( numValues > 0 );

    if ( mId.empty() )
    {
        mLastError = XsError( FATAL_XS_ERROR, "Trying to read from memory before querying its parameters!" );
        return mLastError;
    }

    // Now read the values starting from the given address.
    BitBuffer mem_vals;
    mLastError = HostIoCmd( mId, BitBuffer( address, mAddressWidth ) + READ_OPCODE, mDataWidth * ( numValues + 1 ), mem_vals );

    // Convert data bitstream into individual, multi-bit words and place them in output queue.
    mem_vals.pop_front( mDataWidth );
    while ( !mem_vals.empty() )
    {
        rValues.push_back( mem_vals.front( mDataWidth ) );
        mem_vals.pop_front( mDataWidth );
    }
    assert( rValues.size() == numValues );
    return mLastError;
}



/// Write value to memory device.
///\return An error object.
XsError HostIoToMemory::Write(
    MemoryAddressType const address, ///< Address to write in memory.
    MemoryDataType const    value )  ///< Value to write into memory.
{
    deque<unsigned long long> values;
    values.push_back( value );
    mLastError = Write( address, values );
    return mLastError;
}



/// Write multiple values to sequential addresses in memory device.
///\return An error object.
XsError HostIoToMemory::Write(
    MemoryAddressType const address,   ///< Starting address to write in memory.
    MemoryDataQueue const   &rValues ) ///< Values to write into memory.
{
    assert( rValues.size() > 0 );

    if ( mId.empty() ) // Error if memory parameters not queried before trying to write it.
    {
        mLastError = XsError( FATAL_XS_ERROR, "Trying to write to memory before querying its parameters!" );
        return mLastError;
    }

    // Convert data values into bitstreams.
    BitBuffer values;
    for ( unsigned int i = 0; i < rValues.size(); i++ )
        values.push_back( rValues[i], mDataWidth );

    // Now write data value bitstream to the given memory address.
    BitBuffer null;
    mLastError = HostIoCmd( mId, values + BitBuffer( address, mAddressWidth ) + WRITE_OPCODE, 0, null );
    return mLastError;
}



/// Initialize the memory device object.
///\return An error object.
XsError HostIoToMemory::Init( void )
{
    mLastError = XsError(); // Clear error object.

    return mLastError;
}

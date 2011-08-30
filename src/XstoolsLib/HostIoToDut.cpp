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
 * Object for forcing inputs and reading outputs from a device-under-test (DUT)..
 ***********************************************************************************/

#include "HostIoToDut.h"


/// The opcodes for the operations on a DUT.
BitBuffer const HostIoToDut::NOP_OPCODE( "00" );   ///< No operation.
BitBuffer const HostIoToDut::SIZE_OPCODE( "01" ); ///< Query input and output test vector widths.
BitBuffer const HostIoToDut::WRITE_OPCODE( "10" ); ///< Write test vector to DUT.
BitBuffer const HostIoToDut::READ_OPCODE( "11" );  ///< Read results from DUT.

unsigned int const HostIoToDut::SIZE_RESULT_LENGTH = 16; ///< Length of result from query operation.



/// Default constructor.
HostIoToDut::HostIoToDut( JtagPort *pJtagPort ) ///< Pointer to JTAG port of device.
    : HostIo( pJtagPort )
{
    Init();
}



/// Destructor.
HostIoToDut::~HostIoToDut( void )
{
}



/// Initialize DUT parameters.
///\return An error object.
XsError HostIoToDut::GetSize( unsigned int const id, ///<[in] DUT module identifier.
                             unsigned int &rNumInputs, ///<[out] Number of inputs to DUT.
                             unsigned int &rNumOutputs ///<[out] Number of outputs from DUT.
                             )
{
    mId           = BitBuffer( id, ID_FIELD_LENGTH ); // Store id for this memory.

    // Query DUT for its input and output vector widths.
    BitBuffer params;
    unsigned int const SKIP_CYCLES = 1;
    mLastError      = HostIoCmd( mId, SIZE_OPCODE, SIZE_RESULT_LENGTH + SKIP_CYCLES, params );
    params.pop_front(SKIP_CYCLES);
    mInputWidth = params.front( SIZE_RESULT_LENGTH/2 ); // First 16 bits contain the input vector width.
    params.pop_front( SIZE_RESULT_LENGTH/2 );             // Get rid of the address width.
    mOutputWidth    = params.front( SIZE_RESULT_LENGTH/2 ); // Next 16 bits contain the output result vector width.
    rNumInputs = mInputWidth;
    rNumOutputs = mOutputWidth;
    return mLastError;
}



/// Read result vector from DUT.
///\return An error object.
XsError HostIoToDut::Read( BitBuffer &rResult ) ///< Store outputs from DUT here.
{
    if ( mId.empty() )
    {
        mLastError = XsError( FATAL_XS_ERROR, "Trying to read from DUT before querying its parameters!" );
        return mLastError;
    }

    // Now read the values starting from the given address.
    unsigned int const SKIP_CYCLES = 1;
    mLastError = HostIoCmd( mId, READ_OPCODE, mOutputWidth + SKIP_CYCLES, rResult );
    rResult.pop_front(SKIP_CYCLES);
    assert( rResult.size() == mOutputWidth );
    return mLastError;
}



/// Write test vector to DUT.
///\return An error object.
XsError HostIoToDut::Write( BitBuffer &rVector ) ///< Write this test vector to DUT.
{
    assert( rVector.size() > 0 );

    if ( mId.empty() )
    {
        mLastError = XsError( FATAL_XS_ERROR, "Trying to write to DUT before querying its parameters!" );
        return mLastError;
    }

    // Now write test vector to  the DUT.
    BitBuffer null;
    mLastError = HostIoCmd( mId, rVector + WRITE_OPCODE, 0, null );
    return mLastError;
}



/// Initialize the DUT object.
///\return An error object.
XsError HostIoToDut::Init( void )
{
    mLastError = XsError(); // Clear error object.

    return mLastError;
}

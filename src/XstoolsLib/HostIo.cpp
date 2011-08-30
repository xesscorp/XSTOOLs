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
 *   Object for performing I/O between the host PC and the FPGA board.
 ***********************************************************************************/
#include "HostIo.h"


/// Default constructor.
HostIo::HostIo( JtagPort *pJtagPort ) ///< Pointer to JTAG port of device.
{
    mpJtagPort = NULL;
    Init( pJtagPort );
}



/// Destructor.
HostIo::~HostIo( void )
{
}



/// Reset the HostIo state machine in the device.
///\return An error object.
XsError HostIo::Reset( void )
{
    return Init( NULL );
}



/// Send an id and operand to the device and get the results.
///\return An error object.
XsError HostIo::HostIoCmd(
    BitBuffer const    &id,           // Identifier for the device.
    BitBuffer const    &payload,      // Payload data.
    unsigned int const numResultBits, // Number of result bits to return.
    BitBuffer          &rResults      // Storage for result bits.
    )
{
    XsError error;

    JtagPort &jtag = *mpJtagPort; // Reference to the JTAG port to the device.

    // Create a bit buffer containing the number of operand bits to send and result bits to receive.
    BitBuffer num_payload_bits( payload.size() + numResultBits, NUM_PAYLOAD_BITS_FIELD_LENGTH );

    // Send the id and operand bits to the device. Flush to the device, but do not exit the Shift-DR state.
    error |= jtag.ShiftTdi( payload + num_payload_bits + id, !JtagPort::EXIT_SHIFT, JtagPort::DO_FLUSH );

    // Get any result bits from the device.
    if ( numResultBits != 0 )
        error |= jtag.ShiftTdo( (Port::LengthType)numResultBits, rResults );

    // Store and return any errors.
    mLastError = error;
    return mLastError;
}



/// Initialize the HostIo object.
///\return An error object.
XsError HostIo::Init( JtagPort *pJtagPort ) ///< Pointer to JTAG port of a device.
{
    XsError error;

    // Set the pointer to the lower-level JTAG port.
    if ( pJtagPort != NULL )
        mpJtagPort = pJtagPort;

    // Error if the JTAG port is not set.
    if ( mpJtagPort == NULL )
        return error |= XsError( FATAL_XS_ERROR, "Can't initialize HostIo with a NULL JtagPort pointer!" );

    JtagPort &jtag = *mpJtagPort; // Reference to the JTAG port to the device.

    // Do the following:
    //   1. Reset JTAG TAP FSM.
    //   2. Move TAP FSM to the Shift-IR state.
    //   3. Load in the USER1 instruction.
    //   4. Move TAP FSM to the Shift-DR state.
    //   5. Exit. All HostIo command I/O occurs in the Shift-DR state.
    error |= jtag.ResetTap();
    error |= jtag.GoThruTapStates( RUN_TEST_IDLE, SELECT_DR_SCAN, SELECT_IR_SCAN, CAPTURE_IR, SHIFT_IR, -1 );
    error |= jtag.ShiftTdi( UserInstr(), JtagPort::EXIT_SHIFT, JtagPort::DO_FLUSH );
    error |= jtag.GoThruTapStates( UPDATE_IR, SELECT_DR_SCAN, CAPTURE_DR, SHIFT_DR, -1 );

    // Store and return any errors.
    mLastError = error;
    return mLastError;
}

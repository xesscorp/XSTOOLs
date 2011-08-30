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
 * Low-level and high-level JTAG operations.
 *
 * This object provides JTAG capabilities. It stores the
 * state of the JTAG TAP state machine and updates the state as the TMS and
 * TCK signals change state. It provides methods that make it easier to
 * move between states of the TAP machine and to access the boundary scan
 * instruction and data registers.
 *
 * This object is used with with either the parallel port or USB port object to
 * provide JTAG capabilities to an actual physical port.
 ***********************************************************************************/

#include <cassert>
#include <string>
#include <cstdarg>
#include <algorithm> // For min() function.
#include "UsbCmd.h"
#include "JtagPort.h"

using std::min;
using std::string;


// The following array stores the transition table for the TAP
// controller.  It tells us what the next state will be by placing the
// current state code in the first index and the value of
// the TMS input in the second index.
TapStateType const JtagPort::nextTapState[17][2] =
{
    // TMS=0                 TMS=1            CURRENT TAP STATE
    { INVALID_TAP_STATE, INVALID_TAP_STATE }, // INVALID_STATE
    { RUN_TEST_IDLE, TEST_LOGIC_RESET },      // TEST_LOGIC_RESET
    { RUN_TEST_IDLE, SELECT_DR_SCAN },        // RUN_TEST_IDLE
    { CAPTURE_DR, SELECT_IR_SCAN },           // SELECT_DR_SCAN
    { CAPTURE_IR, TEST_LOGIC_RESET },         // SELECT_IR_SCAN
    { SHIFT_DR, EXIT1_DR },                   // CAPTURE_DR
    { SHIFT_IR, EXIT1_IR },                   // CAPTURE_IR
    { SHIFT_DR, EXIT1_DR },                   // SHIFT_DR
    { SHIFT_IR, EXIT1_IR },                   // SHIFT_IR
    { PAUSE_DR, UPDATE_DR },                  // EXIT1_DR
    { PAUSE_IR, UPDATE_IR },                  // EXIT1_IR
    { PAUSE_DR, EXIT2_DR },                   // PAUSE_DR
    { PAUSE_IR, EXIT2_IR },                   // PAUSE_IR
    { SHIFT_DR, UPDATE_DR },                  // EXIT2_DR
    { SHIFT_IR, UPDATE_IR },                  // EXIT2_IR
    { RUN_TEST_IDLE, SELECT_DR_SCAN },        // UPDATE_DR
    { RUN_TEST_IDLE, SELECT_DR_SCAN },        // UPDATE_IR
};


/// Object constructor. Also serves as default constructor.
JtagPort::JtagPort( Port *pPort ) ///< Physical port object, either USB or LPT.
{
    Init( pPort );
}



/// Transition the TAP FSM through a sequence of TAP states.
///\return An error object.
XsError JtagPort::GoThruTapStates(
    TapStateType nextState, ///< First state to transfer to.
    ... )                   ///< The remaining sequence of states, ending with a -1.
{
    assert( IsBufferEmpty() ); // Transmit buffer should be empty before changing state.

    XsError error;

    // Progress through the states until a -1 is seen.
    va_list ap;
    for ( va_start( ap, nextState ); nextState != -1; nextState = (TapStateType)va_arg( ap, int ) )
    {
        // Check that the current state is valid.
        assert( mTapState >= TEST_LOGIC_RESET && mTapState <= UPDATE_IR );

        // TMS is true (1) if next state is reached by setting TMS=1. TMS is false (0) otherwise.
        bool tms = nextTapState[mTapState][1] == nextState;

        // Put TMS bit into transmit buffer.
        error |= ShiftTms( tms );

        // Check that the next state was reached.
        assert( mTapState == nextState );
    }
    va_end( ap );

    // Transmit the TMS bits to move TAP FSM through the desired states.
    error |= Flush();

    return error; // Return result of operations.
} // GoThruTapStates



/// Transfer the TAP FSM to the Test-Logic-Reset state.
///\return An error object.
XsError JtagPort::ResetTap( void )
{
    assert( IsBufferEmpty() == true ); // Transmit buffer should be empty before reseting.

    XsError error;

    // Five TCK pulses with TMS=1 will always return TAP FSM to Test-Logic-Reset state.
    error    |= ShiftTms( 1 );
    error    |= ShiftTms( 1 );
    error    |= ShiftTms( 1 );
    error    |= ShiftTms( 1 );
    error    |= ShiftTms( 1 );
    error    |= Flush();

    mTapState = TEST_LOGIC_RESET; // This is the state where TAP FSM should be.

    return error;
}



/// Shift a bit buffer of TDI bits into the TDI transmit buffer.
///\return An error object.
XsError JtagPort::ShiftTdi(
    BitBuffer const      tdiBits,   ///< Bits to place into TDI transmit buffer.
    bool const           exitShift, ///< If true, transmit all but last bit with TMS=0, then transmit last bit with TMS=1.
    bool const           doFlush )  ///< If true, flush the transmit buffer after inserting word.
{
    assert( mTmsBitBuffer.empty() ); // In shift states, TMS isn't changed until all TDI bits are sent.
    assert( mTapState == SHIFT_DR || mTapState == SHIFT_IR ); // Must be in this state to shift TDI or TDO.

    XsError error;

    mTdiBitBuffer.push_back(tdiBits); // Put new bits onto end of TDI bit buffer.
   
    if ( exitShift )
        ShiftTms(1); // Send a TMS bit of '1' if exiting the Shift-DR state.

    if ( doFlush )
        error |= Flush(); // Flush the TDI & TMS bits to the device.

    return error;
}



/// Retrieve a specified number of TDO bits from the port.
///\return An error object.
XsError JtagPort::ShiftTdo(
    Port::LengthType const numBits,    ///< Number of TDO bits to retrieve.
    BitBuffer              &rTdoBuffer,   ///< Bit buffer to hold TDO bits.
    bool const             exitShift ) ///< If true, exit TAP shift state after last TDO bit.
{
    assert( IsBufferEmpty() ); // TDI & TMS bits should already be transmitted before receiving TDO bits.
    assert( mTapState == SHIFT_DR || mTapState == SHIFT_IR ); // Must be in this state to shift TDI or TDO.

    XsError error;
    Port::BufferType cmd; // Buffer for holding command to read TDO bits from device.
    Port::BufferType rcv_buffer; // Buffer for receiving TDO bits (packed into words) from device.

    if ( exitShift )
    { // Read TDO bits from device and then exit Shift-DR or Shift-IR state.
        // Get the first N-1 TDO bits before the TAP FSM leaves the shift state.
        error |= ShiftTdo( numBits - 1, rTdoBuffer, false );

        // Send the command to get the last TDO bit as the TAP FMS leaves the shift state.
        Port::BufferType last_tdo; // Last TDO bit goes into this buffer.
        ShiftTms( 1 ); // TMS=1 causes exit of shift state in our internal copy of the TAP state.
        mTmsBitBuffer.clear(); // We just wanted to change our copy of the TMS state. We don't want to actually send TMS=1.
        error |= PrependJtagCmdHdr( 1, GET_TDO_MASK | TMS_VAL_MASK, cmd ); // Prepare command to get 1 TDO bit with TMS=1.
        error |= mpPhysPort->Write(cmd); // Send the command to the physical device.

        // Get the last TDO bit.
        error |= mpPhysPort->Read( 1, rcv_buffer );

        // Put the last bit into the TDO buffer.
        rTdoBuffer.push_back(rcv_buffer.front(),1);
    }
    else
    { // Read TDO bits from device but remain in the Shift-DR or Shift-IR state.
        error |= PrependJtagCmdHdr( numBits, GET_TDO_MASK, cmd ); // Prepare command to get bits with TMS=0.
        error |= mpPhysPort->Write(cmd); // Send the command to the physical device.

        // Now read the TDO bits (packed into words) from the physical device.
        Port::LengthType num_words = ( numBits + Port::DATA_LENGTH - 1 ) / Port::DATA_LENGTH;
        error |= mpPhysPort->Read( num_words, rcv_buffer );

        // Place the packed bits into the TDO buffer.
        Port::LengthType i;
        for(i = numBits; i>=Port::DATA_LENGTH; i-=Port::DATA_LENGTH)
        {
            rTdoBuffer.push_back(rcv_buffer.front(),Port::DATA_LENGTH);
            rcv_buffer.pop_front();
        }
        assert(rcv_buffer.size()<=1);
        if( i != 0)
            rTdoBuffer.push_back(rcv_buffer.front(),i);
    }

    return error;
} // ShiftTdo



/// Pulse the TCK pin a specified number of times.
///\return An error object.
XsError JtagPort::RunTest( unsigned int const numTcks ) ///<  Number of TCK pulses to generate.
{
    XsError error;

    Port::BufferType cmd;
    cmd.push_front( ( numTcks >> 24 ) & 0xFF );
    cmd.push_front( ( numTcks >> 16 ) & 0xFF );
    cmd.push_front( ( numTcks >> 8 ) & 0xFF );
    cmd.push_front( ( numTcks >> 0 ) & 0xFF );
    cmd.push_front( RUNTEST_CMD );

    error |= mpPhysPort->Write( cmd );

    error |= mpPhysPort->Read( 5, cmd );
    assert( cmd.front() == RUNTEST_CMD );

    return error;
}



/// Set the physical port this object talks to.
///\return An error object.
XsError JtagPort::PhysPort( Port *const pPort ) ///< Pointer to USB or LPT port o bject.
{
    mpPhysPort = pPort;
    return XsError( NO_XS_ERROR );
}



/// Get the physical port this object talks to.
///\return The pointer to the physical port.
Port *JtagPort::PhysPort( void )
{
    return mpPhysPort;
}



/// Initialize the object.
///\return An error object.
XsError JtagPort::Init( Port *pPort ) ///< Pointer to physical port object, either USB or LPT.
{
    mTapState  = INVALID_TAP_STATE;
    mpPhysPort = pPort;
    return XsError( NO_XS_ERROR );
}



/// Is the buffer empty of data to send to the port?
///\return True if buffers are empty, false if not.
bool JtagPort::IsBufferEmpty( void )
{
    return mTmsBitBuffer.empty() && mTdiBitBuffer.empty();
}



/// Shift a TMS bit into the transmit buffer and update the TAP FSM state.
///\return An error object.
XsError JtagPort::ShiftTms( bool bit ) ///< Bit to place into transmit buffer.
{
    XsError error;

    // Push the TMS bit into the TMS bit buffer.
    mTmsBitBuffer.push_back( bit );

    // Update the TAP FSM state.
    mTapState = nextTapState[mTapState][bit ? 1 : 0];

    return XsError( NO_XS_ERROR );
}



/// Transmit the contents of the TMS & TDI buffers to the physical port.
///\return An error object.
XsError JtagPort::Flush( void )
{
    assert( !IsBufferEmpty() ); // Why are we flushing an empty buffer? It needs a header (at least).
    assert( mpPhysPort != NULL );       // Physical port must be present to flush anything.

    XsError error;
    Port::BufferType tms_buffer;
    Port::BufferType tdi_buffer;
    Port::BufferType write_buffer;

    if ( mTdiBitBuffer.empty() )
    {
        // Sending only TMS bits.
        error |= PrependJtagCmdHdr( mTmsBitBuffer.size(), PUT_TMS_MASK, write_buffer );
        error |= PackBitsIntoWords( mTmsBitBuffer, write_buffer );
    }
    else
    {
        if ( mTmsBitBuffer.empty() )
        {
            // Sending only TDI bits.
            error |= PrependJtagCmdHdr( mTdiBitBuffer.size(), PUT_TDI_MASK, write_buffer );
            error |= PackBitsIntoWords( mTdiBitBuffer, write_buffer );
        }
        else
        {
            // Sending TDI and TMS bits.
            if ( mTmsBitBuffer.size() == mTdiBitBuffer.size() )
            {
                error |= PrependJtagCmdHdr( mTdiBitBuffer.size(), PUT_TDI_MASK | PUT_TMS_MASK, write_buffer );
                error |= PackBitsIntoWords( mTmsBitBuffer, tms_buffer );
                error |= PackBitsIntoWords( mTdiBitBuffer, tdi_buffer );
                error |= InterleaveBuffers( tms_buffer, tdi_buffer, write_buffer );
            }
            else if ( mTmsBitBuffer.size() == 1 )
            {
                BitsType last_tms_bit = mTmsBitBuffer.back();
                mTmsBitBuffer.pop_back();
                BitsType last_tdi_bit = mTdiBitBuffer.back();
                mTdiBitBuffer.pop_back();
                error |= Flush(); // Send the first N-1 TDI bits.
                mTmsBitBuffer.push_back( last_tms_bit );
                mTdiBitBuffer.push_back( last_tdi_bit );
                error |= Flush(); // Send the last TMS and TDI bits.
                return error;
            }
            else
            {
                // Error - sending mismatched sets of TDI and TMS bits.
                assert( 1 == 0 );
                error |= XsError( FATAL_XS_ERROR, "Mismatched # of TMS and TDI bits" );
                return error;
            }
        }
    }

    assert( !write_buffer.empty() ); // Write buffer better have something to send!

    // Transmit the word buffer.
    error |= mpPhysPort->Write( write_buffer );

    assert( IsBufferEmpty() ); // Bit buffers should be empty after a flush.

    return error;
} // Flush




/// Convert bit buffer into a word buffer that the physical port can transmit.
///\return An error object.
XsError JtagPort::PackBitsIntoWords(
    BitBuffer        &rBits,   ///< Bit buffer.
    Port::BufferType &rWords   ///< Word buffer that gets packed with bits.
    ) const
{
    assert( !rBits.empty() ); // There should be bits to pack.

    // Assemble bits into words and transfer them into the word transmit buffer.
    while ( rBits.size() > 0 )
    {
        unsigned int chunk_size = min( (unsigned int)Port::DATA_LENGTH, (unsigned int)rBits.size() );
        rWords.push_back( rBits.front( chunk_size ) );
        rBits.pop_front( chunk_size );
    }
    assert(rBits.empty());
    assert(!rWords.empty());

    return XsError( NO_XS_ERROR );
}



/// Interleave the contents of two buffers and store them in a third buffer.
///\return An error object.
XsError JtagPort::InterleaveBuffers(
    Port::BufferType &rBuffer1, ///< Buffer whose contents are at odd locations in result.
    Port::BufferType &rBuffer2, ///< Buffer whose contents are at even locations in result.
    Port::BufferType &rResult   ///< Buffer that stores interleaved contents.
    ) const
{
    assert( rBuffer1.size() == rBuffer2.size() );

    while ( !rBuffer1.empty() )
    {
        rResult.push_back( rBuffer1.front() );
        rResult.push_back( rBuffer2.front() );
        rBuffer1.pop_front();
        rBuffer2.pop_front();
    }
    assert(rBuffer1.empty());
    assert(rBuffer2.empty());
    assert(!rResult.empty());

    return XsError( NO_XS_ERROR );
}



/// Place command header for sending TDI and/or TMS bits onto beginning of transmit buffer.
///\return An error object.
XsError JtagPort::PrependJtagCmdHdr(
    Port::LengthType const   numBits,   ///< Number of bits to send/receive with this command.
    JtagCmdFlagsType const flags,     ///< TMS/TDI control flags.
    Port::BufferType         &rBuffer ) ///< Transmit buffer for storing command header.
{
    rBuffer.push_front( flags );
    rBuffer.push_front( ( numBits >> 24 ) & 0xFF );
    rBuffer.push_front( ( numBits >> 16 ) & 0xFF );
    rBuffer.push_front( ( numBits >> 8  ) & 0xFF );
    rBuffer.push_front( ( numBits >> 0  ) & 0xFF );
    rBuffer.push_front( JTAG_CMD );
    return XsError( NO_XS_ERROR );
}

ostream& operator << (ostream& os, Port::BufferType b)
{
    for(unsigned int i=0; i<b.size(); i++)
        os << std::hex << (int)b[i] << " ";
    return os;
}



/// Get the name of the given TAP state.
///\return The string associated with a given TAP state.
string JtagPort::GetTapStateLabel( TapStateType const s ) ///< TAP state.
{
    switch ( s )
    {
        case TEST_LOGIC_RESET:
            return string( "Test-Logic-Reset" );

        case RUN_TEST_IDLE:
            return string( "Run-Test/Idle" );

        case SELECT_DR_SCAN:
            return string( "Select_DR-Scan" );

        case SELECT_IR_SCAN:
            return string( "Select_IR-Scan" );

        case CAPTURE_DR:
            return string( "Capture-DR" );

        case CAPTURE_IR:
            return string( "Capture-IR" );

        case SHIFT_DR:
            return string( "Shift-DR" );

        case SHIFT_IR:
            return string( "Shift-IR" );

        case EXIT1_DR:
            return string( "Exit1-DR" );

        case EXIT1_IR:
            return string( "Exit1-IR" );

        case PAUSE_DR:
            return string( "Pause-DR" );

        case PAUSE_IR:
            return string( "Pause-IR" );

        case EXIT2_DR:
            return string( "Exit2-DR" );

        case EXIT2_IR:
            return string( "Exit2-IR" );

        case UPDATE_DR:
            return string( "Update-DR" );

        case UPDATE_IR:
            return string( "Update-IR" );

        case INVALID_TAP_STATE:
        default:
            assert( true == false ); // should never get here!!
    } // switch
    return string( "Unknown TAP state" );
} // GetTapStateLabel

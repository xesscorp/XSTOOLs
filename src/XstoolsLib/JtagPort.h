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

#ifndef JtagPort_h
#define JtagPort_h


#include <string>
#include "XsError.h"
#include "BitBuffer.h"
#include "Port.h"

using std::string;


namespace XstoolsNamespace
{
/// Identifiers for all possible TAP states.
typedef enum
{
    INVALID_TAP_STATE = 0,  ///< Invalid TAP state
    TEST_LOGIC_RESET  = 1,  ///< Test-Logic-Reset TAP state
    RUN_TEST_IDLE     = 2,  ///< Run-Test/Idle TAP state
    SELECT_DR_SCAN    = 3,  ///< Select-DR-Scan TAP state
    SELECT_IR_SCAN    = 4,  ///< Select-IR-Scan TAP state
    CAPTURE_DR        = 5,  ///< Capture-DR TAP state
    CAPTURE_IR        = 6,  ///< Capture-IR TAP state
    SHIFT_DR          = 7,  ///< Shift-DR TAP state
    SHIFT_IR          = 8,  ///< Shift-IR TAP state
    EXIT1_DR          = 9,  ///< Exit1-DR TAP state
    EXIT1_IR          = 10, ///< Exit1-IR TAP state
    PAUSE_DR          = 11, ///< Pause-DR TAP state
    PAUSE_IR          = 12, ///< Pause-IR TAP state
    EXIT2_DR          = 13, ///< Exit2-DR TAP state
    EXIT2_IR          = 14, ///< Exit2-IR TAP state
    UPDATE_DR         = 15, ///< Update-DR TAP state
    UPDATE_IR         = 16  ///< Update-IR TAP state
} TapStateType;

/// This object translates JTAG operations into a format suitable for
/// the lower-level physical USB or LPT port object.
class JtagPort
{
public:
    static bool const EXIT_SHIFT = true; ///< Flag for exiting Shift-DR or Shift-IR state.
    static bool const DO_FLUSH   = true; ///< Flag for forcing flush of transmit buffers.

    /// Object constructor. Also serves as default constructor.
    JtagPort( Port *pPort = NULL ); ///< Physical port object, either USB or LPT.

    /// Transition the TAP FSM through a sequence of TAP states.
    ///\return An error object.
    XsError GoThruTapStates(
        TapStateType state, ///< First state to transfer to.
        ... );              ///< The remaining sequence of states, ending with a -1.

    /// Transfer the TAP FSM to the Test-Logic-Reset state.
    ///\return An error object.
    XsError ResetTap( void );

    /// Shift a bit buffer of TDI bits into the TDI transmit buffer.
    ///\return An error object.
    XsError ShiftTdi(
        BitBuffer const      tdiBits,   ///< Bits to place into TDI transmit buffer.
        bool const           exitShift=false, ///< If true, transmit all but last bit with TMS=0, then transmit last bit with TMS=1.
        bool const           doFlush=false ); ///< If true, flush the transmit buffer after inserting word.

    /// Retrieve a specified number of TDO bits from the port.
    ///\return An error object.
    XsError ShiftTdo(
        Port::LengthType const numBits,    ///< Number of TDO bits to retrieve.
        BitBuffer              &rTdoBuffer,   ///< Bit buffer to hold TDO bits.
        bool const             exitShift=false ); ///< If true, exit TAP shift state after last TDO bit.

    /// Pulse the TCK pin a specified number of times.
    ///\return An error object.
    XsError RunTest( unsigned int const numTcks ); ///< Number of TCK pulses to generate.

    /// Set the physical port this object talks to.
    ///\return An error object.
    XsError PhysPort( Port *const pPort ); ///< Pointer to USB or LPT port object.

    /// Get the physical port this object talks to.
    ///\return The pointer to the physical port.
    Port *PhysPort( void );

private:
    typedef Port::DataType JtagCmdFlagsType; ///< Type for flags sent with TAP_SEQ_CMD.

    static JtagCmdFlagsType const GET_TDO_MASK = 0x01; // Set if gathering TDO bits.
    static JtagCmdFlagsType const PUT_TMS_MASK = 0x02; // Set if TMS bits are included in the packets.
    static JtagCmdFlagsType const TMS_VAL_MASK = 0x04; // Static value for TMS if PUT_TMS_MASK is cleared.
    static JtagCmdFlagsType const PUT_TDI_MASK = 0x08; // Set if TDI bits are included in the packets.
    static JtagCmdFlagsType const TDI_VAL_MASK = 0x10; // Static value for TDI if PUT_TDI_MASK is cleared.

    static unsigned int const EXIT_SHIFT_TMS_VAL = 1; ///< Value of TMS when leaving Shift-DR or Shift-IR state.

    // The following array stores the transition table for the TAP
    // controller.  It tells us what the next state will be by placing the
    // current state code in the first index and the value of
    // the TMS input in the second index.
    static TapStateType const nextTapState[17][2];

    Port *mpPhysPort;        ///< Pointer to USB or LPT port that accepts/delivers data.
    TapStateType mTapState;  ///< State of Test Access Port
    BitBuffer mTmsBitBuffer; ///< Buffer for TMS bits.
    BitBuffer mTdiBitBuffer; ///< Buffer for TDI bits.

    /// Initialize the object.
    ///\return An error object.
    XsError Init( Port *const pPort ); ///< Pointer to physical port object, either USB or LPT.

    /// Is the buffer empty of data to send to the port?
    ///\return True if buffers are empty, false if not.
    bool IsBufferEmpty( void );

    /// Shift a TMS bit into the transmit buffer and update the TAP FSM state.
    ///\return An error object.
    XsError ShiftTms( bool const bit ); ///< Bit to place into transmit buffer.

    /// Transmit the contents of the buffer to the physical port.
    ///\return An error object.
    XsError Flush( void );

    /// Convert bit buffer into a word buffer that the physical port can transmit.
    ///\return An error object.
    XsError PackBitsIntoWords(
        BitBuffer        &rBits,    ///< Bit buffer.
        Port::BufferType &rWords    ///< Word buffer that gets packed with bits.
        ) const;

    /// Interleave the contents of two word buffers and store them in a third buffer.
    ///\return An error object.
    XsError InterleaveBuffers(
        Port::BufferType &rBuffer1,  ///< Buffer whose contents are at odd locations in result.
        Port::BufferType &rBuffer2,  ///< Buffer whose contents are at even locations in result.
        Port::BufferType &rResult    ///< Buffer that stores interleaved contents.
        ) const;

    /// Place command header for sending TDI and/or TMS bits onto beginning of transmit buffer.
    ///\return An error object.
    XsError PrependJtagCmdHdr(
        Port::LengthType const   numBits,    ///< Number of bits to send/receive with this command.
        JtagCmdFlagsType const flags,      ///< TMS/TDI control flags.
        Port::BufferType         &rBuffer ); ///< Transmit buffer for storing command header.

    /// Get the name of the given TAP state.
    ///\return The string associated with a given TAP state.
    string GetTapStateLabel( TapStateType const s ); ///< TAP state.
};
} // XstoolsNamespace

using namespace XstoolsNamespace;

ostream & operator << (ostream &os, Port::BufferType b); 

#endif

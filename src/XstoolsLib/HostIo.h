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
#ifndef HostIo_h
#define HostIo_h

#include <cassert>
#include <string>
#include "XsError.h"
#include "BitBuffer.h"
#include "JtagPort.h"

using std::string;


namespace XstoolsNamespace
{
/// Lengths of bitfields in bitstream to the HostIo module in the FPGA.
unsigned int const ID_FIELD_LENGTH               = 8;  /// Module Identifier length.
unsigned int const NUM_PAYLOAD_BITS_FIELD_LENGTH = 32; /// #Payload bits length.

/// This object is the entry-point for doing I/O between the host PC and the FPGA board.
class HostIo
{
public:
    /// Default constructor.
    HostIo( JtagPort *pJtagPort = NULL );

    /// Destructor.
    ~HostIo( void );

    /// Reset the HostIo state machine in the device.
    ///\return An error object.
    XsError Reset( void );

    /// Send an opcode and operand to the device and get the results.
    ///\return An error object.
    XsError HostIoCmd(
        BitBuffer const    &id,           // Identifier for the device.
        BitBuffer const    &payload,      // Payload data.
        unsigned int const numResultBits, // Number of result bits to return.
        BitBuffer          &rResults      // Storage for result bits.
        );

    /// Access routines.
    BitBuffer &UserInstr( void ) { return mUserInstr; }

protected:
    XsError mLastError;          /// The last error this module has seen.

private:
    JtagPort *mpJtagPort; /// Stores the pointer to the port to the physical device.
    BitBuffer mUserInstr;  /// Stores the USER instruction that enables HostIo to work.

    /// Initialize the HostIo object.
    ///\return An error object.
    XsError Init( JtagPort *pJtagPort ); ///< Pointer to JTAG port of a device.
};
} // XstoolsNamespace

using namespace XstoolsNamespace;

#endif

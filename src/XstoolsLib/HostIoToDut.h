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

#ifndef HostIoToDut_h
#define HostIoToDut_h

#include <queue>
#include "HostIo.h"

using std::deque;


namespace XstoolsNamespace
{
/// Object for performing memory-mapped I/O between the host PC and the FPGA board.
class HostIoToDut : public HostIo
{
public:
    /// Default constructor.
    HostIoToDut( JtagPort *pJtagPort = NULL );

    /// Destructor.
    ~HostIoToDut( void );

    /// Initialize memory parameters.
    ///\return An error object.
    XsError GetSize(
        unsigned int const id,          ///<[in] DUT module identifier.
        unsigned int       &rNumInputs, ///<[out] Number of inputs to DUT.
        unsigned int       &rNumOutputs ///<[out] Number of outputs from DUT.
        );

    /// Read result vector from DUT.
    ///\return An error object.
    XsError Read( BitBuffer &rResult ); ///< Store result from DUT here.

    /// Write test vector to DUT.
    ///\return An error object.
    XsError Write( BitBuffer &rVector ); ///< Write this test vector to DUT.

private:
    /// The opcodes for the operations a memory device can perform.
    static BitBuffer const NOP_OPCODE;
    static BitBuffer const SIZE_OPCODE;
    static BitBuffer const WRITE_OPCODE;
    static BitBuffer const READ_OPCODE;

    ///< Length of result from query operation.
    static unsigned int const SIZE_RESULT_LENGTH;

    BitBuffer mId;             ///< DUT module ID.
    unsigned int mInputWidth;  ///< Width of DUT input vector.
    unsigned int mOutputWidth; ///< Width of DUT output result vector.

    /// Initialize the memory device object.
    XsError Init( void );
};
} // XstoolsNamespace

using namespace XstoolsNamespace;

#endif

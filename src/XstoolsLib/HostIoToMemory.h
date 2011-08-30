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

#ifndef HostIoToMemory_h
#define HostIoToMemory_h

#include <queue>
#include "HostIo.h"

using std::deque;


namespace XstoolsNamespace
{
/// Object for performing memory-mapped I/O between the host PC and the FPGA board.
class HostIoToMemory : public HostIo
{
public:
    typedef unsigned long long MemoryAddressType;
    typedef unsigned long long MemoryDataType;
    typedef deque<MemoryDataType> MemoryDataQueue;

    /// Default constructor.
    HostIoToMemory( JtagPort *pJtagPort = NULL );

    /// Destructor.
    ~HostIoToMemory( void );

    /// Initialize memory parameters.
    ///\return An error object.
    XsError GetSize(
        unsigned int const id,             ///< Memory module identifier.
        unsigned int       &rAddressWidth, ///< Address width.
        unsigned int       &rDataWidth     ///< Data width.
        );

    /// Read value from memory device.
    ///\return An error object.
    XsError Read(
        MemoryAddressType address,   ///< Address to read from memory.
        MemoryDataType    &rValue ); ///< Store value read from memory here.

    /// Read multiple, sequential addresses from memory device.
    ///\return An error object.
    XsError Read(
        MemoryAddressType const address,    ///< Starting address for reading memory.
        MemoryAddressType const numValues,  ///< Number of values to get from memory.
        MemoryDataQueue         &rValues ); ///< Queue for storing values.

    /// Write value to memory device.
    ///\return An error object.
    XsError Write(
        MemoryAddressType const address, ///< Address to write in memory.
        MemoryDataType const    value ); ///< Value to write into memory.

    /// Write multiple values to sequential addresses in memory device.
    ///\return An error object.
    XsError Write(
        MemoryAddressType const address,    ///< Starting address to write in memory.
        MemoryDataQueue const   &rValues ); ///< Values to write into memory.

private:
    /// The opcodes for the operations a memory device can perform.
    static BitBuffer const NOP_OPCODE;
    static BitBuffer const SIZE_OPCODE;
    static BitBuffer const WRITE_OPCODE;
    static BitBuffer const READ_OPCODE;

    /// Length of result from query operation.
    static unsigned int const SIZE_RESULT_LENGTH;

    BitBuffer mId;              /// Memory module ID.
    unsigned int mAddressWidth; /// Memory address width.
    unsigned int mDataWidth;    /// Memory data width.

    /// Initialize the memory device object.
    XsError Init( void );
};
} // XstoolsNamespace

using namespace XstoolsNamespace;

#endif

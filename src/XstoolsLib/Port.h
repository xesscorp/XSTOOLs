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
 *  Base port object that is used for writing/reading to/from a peripheral device.
 ***********************************************************************************/

#ifndef Port_h
#define Port_h


#include <queue>     // For queues.
#include "xserror.h" // For error objects.

using std::deque;


namespace XstoolsNamespace
{
/// Base USB object for read or write of a particular USB device endpoint.
///
/// Base USB object that is used for writing/reading to/from an endpoint
/// of a particular instance of a USB device as identified by VID and PID.
class Port
{
public:
    typedef unsigned char DataType;           ///< Smallest piece of data to/from USB device.
    typedef  deque<DataType> BufferType;      ///< Buffered data.
    typedef BufferType::size_type LengthType; ///< Length of data buffer.
    typedef long int TimeoutType;             ///< Timeout interval.

    static unsigned int const DATA_LENGTH    = 8 * sizeof( DataType );
    static TimeoutType const DEFAULT_TIMEOUT = 100;

    /// Create a port object.
    ///\return Nothing.
    Port( void ) {};

    /// Destroy a port object.
    ///\return Nothing.
    virtual ~Port() {};

    /// Open input and output endpoints of a port object.
    ///\return Error object.
    virtual XsError Open( unsigned int const numTrials = 1 ) = 0;

    /// Read from a device into a buffer.
    ///\return Error object.
    virtual XsError Read(
        LengthType const  rqstdLength,                ///< Requested number of bytes to read.
        BufferType        &rDataFromDevice,           ///< Buffer to hold data read from device.
        TimeoutType const timeoutMs = DEFAULT_TIMEOUT ///< Timeout in milliseconds.
        ) = 0;

    /// Write to a device from a buffer.
    ///\return Error object.
    virtual XsError Write(
        BufferType        &rDataToDevice,             ///< Buffer holding data to write to device.
        TimeoutType const timeoutMs = DEFAULT_TIMEOUT ///< Timeout in milliseconds.
        )                         = 0;

    /// Close the input and output endpoints of a port object.
    ///\return Error object.
    virtual XsError Close( void ) = 0;
};
} // XstoolsNamespace

using namespace XstoolsNamespace;

#endif

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
 *  Base USB object that is used for writing/reading to/from an endpoint
 *  of a particular instance of a USB device as identified by VID and PID.
 ***********************************************************************************/

#ifndef UsbPort_h
#define UsbPort_h


#include "Port.h"
#include "XsError.h" // For error objects.

namespace XstoolsNamespace
{
typedef int VidType;      ///< USB vendor ID.
typedef int PidType;      ///< USB product ID.
typedef int InstanceType; ///< Particular instance of USB device with given VID and PID.
typedef int EndpointType; ///< USB endpoint.


/// Base USB object for read or write of a particular USB device endpoint.
///
/// Base USB object that is used for writing/reading to/from an endpoint
/// of a particular instance of a USB device as identified by VID and PID.
class UsbPort : public Port
{
public:
    static VidType const INVALID_VID           = -1;
    static PidType const INVALID_PID           = -1;
    static InstanceType const INVALID_INSTANCE = -1;
    static EndpointType const INVALID_ENDPOINT = -1;

    /// Create a USB port object.
    ///\return Nothing.
    UsbPort(
        VidType      vid = INVALID_VID,           ///< USB vendor ID.
        PidType      pid = INVALID_PID,           ///< USB product ID.
        InstanceType instance = INVALID_INSTANCE, ///< Instance of USB device with given VID & PID.
        EndpointType endpoint = INVALID_ENDPOINT  ///< Endpoint of given USB device.
        );

    /// Destroy a USB port object.
    ///\return Nothing.
    virtual ~UsbPort() {};

    /// Determine the number of instances of a USB ports with this VID and PID.
    ///\return The number of USB ports.
    virtual unsigned int GetUsbPortCount(
        VidType const vid, ///< USB vendor ID.
        PidType const pid  ///< USB product ID.
        ) const = 0;

    /// Accessor for the USB vendor ID.
    ///\return Vendor ID.
    VidType &Vid( void );

    /// Accessor for the USB product ID.
    ///\return Product ID.
    PidType &Pid( void );

    /// Accessor for the USB port instance.
    ///\return Port instance.
    InstanceType &Instance( void );

    /// Accessor for the USB endpoint number.
    ///\return Endpoint number.
    EndpointType &Endpoint( void );

private:
    VidType mVid;           ///< USB vendor ID.
    PidType mPid;           ///< USB product ID.
    InstanceType mInstance; ///< particular instance of this object among all such objects
    EndpointType mEndpoint; ///< USB endpoint associated with this object

    /// Initialize a USB port object.
    ///\return Error object.
    XsError Init(
        VidType const      vid,      ///< USB vendor ID.
        PidType const      pid,      ///< USB product ID.
        InstanceType const instance, ///< Instance of USB device with given VID & PID.
        EndpointType const endpoint  ///< Endpoint of given USB device.
        );
};
} // XstoolsNamespace

using namespace XstoolsNamespace;

#endif

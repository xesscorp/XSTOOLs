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


#include "UsbPort.h"


/// Create a USB port object.
///\return Nothing.
UsbPort::UsbPort(
    VidType const      vid,      ///< USB vendor ID.
    PidType const      pid,      ///< USB product ID.
    InstanceType const instance, ///< Instance of USB device with given VID & PID.
    EndpointType const endpoint  ///< Endpoint of given USB device.
    )
{
    Init( vid, pid, instance, endpoint );
}



/// Accessor for the USB vendor ID.
///\return Vendor ID.
VidType &UsbPort::Vid( void )
{
    return mVid;
}



/// Accessor for the USB product ID.
///\return Product ID.
PidType &UsbPort::Pid( void )
{
    return mPid;
}



/// Accessor for the USB port instance.
///\return Port instance.
InstanceType &UsbPort::Instance( void )
{
    return mInstance;
}



/// Accessor for the USB endpoint number.
///\return Endpoint number.
EndpointType &UsbPort::Endpoint( void )
{
    return mEndpoint;
}


/// Initialize a USB port object.
///\return Error object.
XsError UsbPort::Init(
    VidType const      vid,      ///< USB vendor ID.
    PidType const      pid,      ///< USB product ID.
    InstanceType const instance, ///< Instance of USB device with given VID & PID.
    EndpointType const endpoint  ///< Endpoint of given USB device.
    )
{
    mVid      = vid;
    mPid      = pid;
    mInstance = instance;
    mEndpoint = endpoint;
    return XsError( NO_XS_ERROR );
}

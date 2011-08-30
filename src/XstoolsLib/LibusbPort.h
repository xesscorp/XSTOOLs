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
 *   ©1997-2011 - X Engineering Software Systems Corp. (www.xess.com)
 ***********************************************************************************/

/***********************************************************************************
 * USB port object that interfaces to the libusb driver.
 ***********************************************************************************/

#ifndef LibusbPort_h
#define LibusbPort_h

#include "UsbPort.h" // For UsbPort object.

namespace XstoolsNamespace
{
/// This object adds methods/members to the UsbPort object to support the libusb driver.
class LibusbPort : public UsbPort
{
public:
    /// Create a USB port object.
    ///\return Nothing.
    LibusbPort(
        VidType      vid = INVALID_VID,           ///< USB vendor ID.
        PidType      pid = INVALID_PID,           ///< USB product ID.
        InstanceType instance = INVALID_INSTANCE, ///< Instance of USB device with given VID & PID.
        EndpointType endpoint = INVALID_ENDPOINT  ///< Endpoint of given USB device.
        );

    /// Destroy a USB port object.
    ///\return Nothing.
    ~LibusbPort();

    /// Determine the number of instances of a USB port with this VID and PID.
    ///\return The number of USB ports.
    unsigned int GetUsbPortCount(
        VidType const vid, ///< USB vendor ID.
        PidType const pid  ///< USB product ID.
        ) const;

    /// Open input and output endpoints of a USB port object.
    ///\return Error object.
    XsError Open( unsigned int const numTrials = 1 ); ///< try this number of times to open the device

    /// Read from a USB device into a buffer.
    ///\return Error object.
    XsError Read(
        LengthType const  rqstdLength,                ///< Requested number of bytes to read.
        BufferType        &rDataFromDevice,           ///< Buffer to hold data read from device.
        TimeoutType const timeoutMs = DEFAULT_TIMEOUT ///< Timeout in milliseconds.
        );

    /// Write to a USB device from a buffer.
    ///\return Error object.
    XsError Write(
        BufferType        &rDataToDevice,             ///< Buffer holding data to write to device.
        TimeoutType const timeoutMs = DEFAULT_TIMEOUT ///< Timeout in milliseconds.
        );

    /// Close the input and output endpoints of a USB port object.
    ///\return Error object.
    XsError Close( void );

private:
    // Direction of transfer between host and USB peripheral.
    typedef enum
    {
        DIR_PERIPH_TO_HOST,
        DIR_HOST_TO_PERIPH
    } UsbDirectionType;

    // Extended handle that holds the libusb device handle and the endpoint.
    typedef struct
    {
        bool                  mIsOpen;     ///< True when device is opened for read/write operations.
        struct usb_dev_handle *mDevHandle; ///< libusb device handle. Valid only when open.
        int                   mEndpoint;   ///< Device endpoint. Valid only when open.
    } HandleType;

    HandleType mHandleFromPeriph; ///< handle for endpoint that receives data from a USB peripheral
    HandleType mHandleToPeriph;   ///< handle for endpoint that sends data to a USB peripheral

    /// This flag is used to make sure the libusb library is only initialized once.
    static bool mIsLibusbInitialized;

    /// Initialize the USB port object.
    ///\return Nothing.
    void Init( void );

    /// Initialize libusb.
    ///\return Nothing.
    static void LibusbInit( void );

    /// Get the number of libusb devices with the given USB vendor and product IDs.
    ///\return Number of devices found.
    static unsigned int LibusbGetDeviceCount(
        VidType vid, ///< 16-bit vendor ID.
        PidType pid  ///< 16-bit product ID.
        );

    /// Open the requested instance of a libusb device with the given USB vendor and product IDs.
    ///\return Error object with results of operation. Device handle is returned in handle argument.
    XsError LibusbOpen(
        UsbDirectionType const dir,     ///< I/O direction.
        HandleType             &rHandle ///< Extended handle for the opened device.
        );

    /// Close the libusb device with the given extended handle.
    ///\return Error object.
    XsError LibusbClose( HandleType &rHandle ); ///< Extended handle for the USB device.
};
} // XstoolsNamespace

using namespace XstoolsNamespace;

#endif

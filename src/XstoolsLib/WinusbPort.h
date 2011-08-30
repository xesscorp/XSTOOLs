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
 * USB port object that interfaces to the Microsoft WINUSB driver.
 ***********************************************************************************/

#ifndef WinusbPort_h
#define WinusbPort_h

#include "UsbPort.h" // For UsbPort object.

namespace XstoolsNamespace
{
/// This object adds methods/members to the UsbPort object to support the WINUSB driver.
class WinusbPort : public UsbPort
{
public:
    /// Create a USB port object.
    ///\return Nothing.
    WinusbPort(
        VidType      vid = INVALID_VID,           ///< USB vendor ID.
        PidType      pid = INVALID_PID,           ///< USB product ID.
        InstanceType instance = INVALID_INSTANCE, ///< Instance of USB device with given VID & PID.
        EndpointType endpoint = INVALID_ENDPOINT  ///< Endpoint of given USB device.
        );

    /// Destroy a USB port object.
    ///\return Nothing.
    ~WinusbPort();

    /// Determine the number of instances of a USB port with this VID and PID.
    ///\return The number of USB ports.
    unsigned int GetUsbPortCount(
        VidType const vid, ///< USB vendor ID.
        PidType const pid  ///< USB product ID.
        ) const;

    /// Open input and output endpoints of a USB port object.
    ///\return Error object.
    XsError Open( unsigned int const numTrials ); ///< try this number of times to open the device

    /// Read from a USB device into a buffer.
    ///\return Error object.
    XsError Read(
        LengthType const  rqstdLength,      ///< Requested number of bytes to read.
        BufferType        &rDataFromDevice, ///< Buffer to hold data read from device.
        TimeoutType const timeoutMs         ///< Timeout in milliseconds.
        );

    /// Write to a USB device from a buffer.
    ///\return Error object.
    XsError Write(
        BufferType        &rDataToDevice, ///< Buffer holding data to write to device.
        TimeoutType const timeoutMs       ///< Timeout in milliseconds.
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

    // Extended handle that holds the WINUSB device handle and the endpoint.
    typedef struct
    {
        bool   mIsOpen;       ///< True when device is opened for read/write operations.
        HANDLE mDevHandle;    ///< WINUSB device handle. Valid only when open.
        HANDLE mWinusbHandle; ///< WINUSB handle. Valid after device has been claimed.
        int    mEndpoint;     ///< Device endpoint. Valid after device has been opened.
        UCHAR  mPipeId;       ///< Endpoint pipe ID.
    } HandleType;

    HandleType mHandleFromPeriph; ///< handle for endpoint that receives data from a USB peripheral
    HandleType mHandleToPeriph;   ///< handle for endpoint that sends data to a USB peripheral

    // Global unique ID for XESS USB interface through WINUSB driver.
    static GUID WinusbPort::XsusbWinusbGuid;

    /// Initialize the USB port object.
    ///\return Nothing.
    void Init( void );

    /// Get the path to a device given its interface GUID and device instance.
    ///\return TRUE if device path was found, FALSE otherwise.
    BOOL WinusbGetDevicePath(
        LPGUID interfaceGuid, ///< interface GUID
        DWORD  instance,      ///< device instance
        WCHAR  *devicePath,   ///< pointer to buffer to hold the path
        size_t bufLen         ///< length of buffer
        );

    /// Open a device with the given interface GUID and instance.
    ///\return Handle to the device or INVALID_HANDLE_VALUE.
    HANDLE WinusbOpenDevice(
        LPGUID interfaceGuid, ///< interface GUID
        DWORD  instance       ///< device instance
        );

    /// Open the requested instance of a WINUSB device with the given USB vendor and product IDs.
    ///\return Error object with results of operation. Device handle is returned in handle argument.
    XsError WinusbPort::WinusbOpen(
        UsbDirectionType const dir,     ///< I/O direction.
        HandleType             &rHandle ///< Extended handle for the opened device.
        );

    /// Claim the opened USB device for I/O operations.
    ///\return An error object.
    XsError WinusbClaim( HandleType &rHandle ); ///< Extended handle for USB device.

    /// Release the opened USB device so someone else can use it.
    ///\return An error object.
    XsError WinusbRelease( HandleType &rHandle ); ///< Extended handle for USB device.

    /// Close a device with the given handle.
    ///\return An error object.
    XsError WinusbCloseDevice( HandleType &rHandle ); ///< Extended handle for the USB device.

    /// Close the libusb device with the given extended handle.
    ///\return Error object.
    XsError WinusbClose( HandleType &rHandle ); ///< Extended handle for the USB device.
};
} // XstoolsNamespace

using namespace XstoolsNamespace;

#endif

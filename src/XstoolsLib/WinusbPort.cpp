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
 * USB port object that interfaces to the Microsoft Winusb driver.
 ***********************************************************************************/

#include <wtypes.h>
#include <winusb.h>
#include <SETUPAPI.h>
#include <cassert>
#include "WinusbPort.h"
#include <strsafe.h> // Keep this last in list to avoid compiler warnings.



// Global unique ID for XESS USB interface through WINUSB driver.
// {19326627-91F6-49c8-9E9F-58B540B79DF2}
GUID WinusbPort::XsusbWinusbGuid
    = {
    0x19326627, 0x91f6, 0x49c8, { 0x9e, 0x9f, 0x58, 0xb5, 0x40, 0xb7, 0x9d, 0xf2 }
    };



/// Create a USB port object.
///\return Nothing.
WinusbPort::WinusbPort(
    VidType      vid,      ///< USB vendor ID.
    PidType      pid,      ///< USB product ID.
    InstanceType instance, ///< Instance of USB device with given VID & PID.
    EndpointType endpoint  ///< Endpoint of given USB device.
    ) : UsbPort( vid, pid, instance, endpoint )
{
    Init();
}



/// Destroy a USB port object.
///\return Nothing.
WinusbPort::~WinusbPort( void )
{
    Close();
}



/// Determine the number of instances of a USB port with this VID and PID.
///\return The number of USB ports.
unsigned int WinusbPort::GetUsbPortCount(
    VidType const vid, ///< USB vendor ID.
    PidType const pid  ///< USB product ID.
    ) const
{
    LPGUID interface_guid = &XsusbWinusbGuid;

    // get info on all the attached devices with this GUID
    HDEVINFO device_info  = SetupDiGetClassDevs( interface_guid, NULL, NULL,
                                                 DIGCF_PRESENT | DIGCF_DEVICEINTERFACE );
    if ( device_info == INVALID_HANDLE_VALUE )
        return 0;

    // count up the attached devices
    SP_DEVICE_INTERFACE_DATA interface_data;
    interface_data.cbSize = sizeof( SP_DEVICE_INTERFACE_DATA );
    unsigned dev_cnt;
    for ( dev_cnt = 0;; dev_cnt++ )
        if ( SetupDiEnumDeviceInterfaces( device_info, NULL, interface_guid, dev_cnt, &interface_data ) == FALSE )
            break;

    // release the device information structure
    SetupDiDestroyDeviceInfoList( device_info );

    // return the number of devices found
    return dev_cnt;
}



/// Open input and output endpoints of a USB port object.
///\return Error object.
XsError WinusbPort::Open( unsigned int const numTrials ) ///< try this number of times to open the device
{
    XsError error;

    // Open channel used to send data to the USB peripheral (if it is not already opened).
    for ( int i = numTrials; i > 0 && !mHandleToPeriph.mIsOpen; i-- )
        error = WinusbOpen( DIR_HOST_TO_PERIPH, mHandleToPeriph );

    if ( !error.IsError() )
        // Open channel used to receive data from the USB peripheral (if it is not already opened).
        for ( int i = numTrials; i > 0 && !mHandleFromPeriph.mIsOpen; i-- )
            error |= WinusbOpen( DIR_PERIPH_TO_HOST, mHandleFromPeriph );

    if ( error.IsError() )
        Close();  // Close the endpoints if an error occurred while opening them.

    return error;
}



/// Read from a USB device into a buffer.
///\return Error object.
XsError WinusbPort::Read(
    LengthType const  rqstdLength,      ///< Requested number of bytes to read.
    BufferType        &rDataFromDevice, ///< Buffer to hold data read from device.
    TimeoutType const timeoutMs         ///< Timeout in milliseconds.
    )
{
    assert( mHandleFromPeriph.mIsOpen == true );
    assert( mHandleFromPeriph.mDevHandle != INVALID_HANDLE_VALUE );
    assert( rqstdLength != 0 );
    assert( timeoutMs < 20000 );

    XsError error;

    // claim the USB interface for I/O
    error = WinusbClaim( mHandleFromPeriph );
    if ( error.IsError() )
        return error;  // couldn't claim it, so return failure

    // set timeout for I/O operation
    DWORD timeout                     = timeoutMs;
    WinUsb_SetPipePolicy( mHandleFromPeriph.mWinusbHandle, mHandleFromPeriph.mEndpoint, PIPE_TRANSFER_TIMEOUT, sizeof( DWORD ), &timeout );

    // Make char array for storing data read from device.
    unsigned char *p_data_from_device = new unsigned char[rqstdLength];

    // read data from the USB device
    ULONG num_bytes_read;
    BOOL succeeded                    = WinUsb_ReadPipe( mHandleFromPeriph.mWinusbHandle, mHandleFromPeriph.mEndpoint, (PUCHAR)p_data_from_device, rqstdLength, &num_bytes_read, NULL );
    if ( !succeeded )
        error |= XsError( MINOR_XS_ERROR, "Read of WINUSB device failed." );

    // Place char data into return buffer.
    if ( !error.IsError() )
        for ( ULONG i = 0; i < num_bytes_read; i++ )
            rDataFromDevice.push_back( p_data_from_device[i] );

    // I/O is done, so release our claim on the USB device
    error |= WinusbRelease( mHandleFromPeriph );

    // Delete the char array.
    delete [] p_data_from_device;

    return error;
} // Read



/// Write to a USB device from a buffer.
///\return Error object.
XsError WinusbPort::Write(
    BufferType        &rDataToDevice, ///< Buffer holding data to write to device.
    TimeoutType const timeoutMs       ///< Timeout in milliseconds.
    )
{
    assert( mHandleToPeriph.mIsOpen == true );
    assert( mHandleToPeriph.mDevHandle != INVALID_HANDLE_VALUE );
    assert( rDataToDevice.size() > 0 );
    assert( timeoutMs < 20000 );

    XsError error;

    // claim the USB interface for I/O
    error = WinusbClaim( mHandleToPeriph );
    if ( error.IsError() )
        return error;  // couldn't claim it, so return failure

    // set timeout for I/O operation
    DWORD timeout                   = timeoutMs;
    WinUsb_SetPipePolicy( mHandleToPeriph.mWinusbHandle, mHandleToPeriph.mEndpoint, PIPE_TRANSFER_TIMEOUT, sizeof( DWORD ), &timeout );

    // Place buffer data into a char array.
    BufferType::size_type size      = rDataToDevice.size();
    BufferType::size_type i;
    unsigned char *p_data_to_device = new unsigned char[rDataToDevice.size()];
    for ( i = 0; i < size; i++ )
    {
        p_data_to_device[i] = rDataToDevice.front();
        rDataToDevice.pop_front();
    }

    // write data to the USB device
    ULONG num_bytes_written = 0;
    BOOL succeeded          = WinUsb_WritePipe( mHandleToPeriph.mWinusbHandle, mHandleToPeriph.mEndpoint, (PUCHAR)p_data_to_device, size, &num_bytes_written, NULL );
    if ( !succeeded )
        error |= XsError( MINOR_XS_ERROR, "Write of WINUSB device failed." );

    // I/O is done, so release our claim on the USB device
    error |= WinusbRelease( mHandleToPeriph );

    // Push any unsent data back into the buffer.
    for ( i = num_bytes_written; i < size; i++ )
        rDataToDevice.push_back( p_data_to_device[i] );

    // Delete the char array.
    delete [] p_data_to_device;

    return error;
} // Write



/// Close the input and output endpoints of a USB port object.
///\return Error object.
XsError WinusbPort::Close( void )
{
    XsError error;

    error  = WinusbClose( mHandleToPeriph );
    error |= WinusbClose( mHandleFromPeriph );
    return error;
}



/// Initialize the WINUSB port object.
///\return Nothing.
void WinusbPort::Init( void )
{
    mHandleToPeriph.mIsOpen         = false;
    mHandleToPeriph.mDevHandle      = INVALID_HANDLE_VALUE;
    mHandleToPeriph.mWinusbHandle   = INVALID_HANDLE_VALUE;
    mHandleToPeriph.mEndpoint       = INVALID_ENDPOINT;

    mHandleFromPeriph.mIsOpen       = false;
    mHandleFromPeriph.mDevHandle    = INVALID_HANDLE_VALUE;
    mHandleFromPeriph.mWinusbHandle = INVALID_HANDLE_VALUE;
    mHandleFromPeriph.mEndpoint     = INVALID_ENDPOINT;
}



/// Get the path to a device given its interface GUID and device instance.
///\return TRUE if device path was found, FALSE otherwise.
BOOL WinusbPort::WinusbGetDevicePath(
    LPGUID interfaceGuid, ///< interface GUID
    DWORD  instance,      ///< device instance
    WCHAR  *devicePath,   ///< pointer to buffer to hold the path
    size_t bufLen         ///< length of buffer
    )
{
    BOOL b_result                                = FALSE;
    HDEVINFO device_info;
    SP_DEVICE_INTERFACE_DATA interface_data;
    PSP_DEVICE_INTERFACE_DETAIL_DATA detail_data = NULL;
    ULONG length;
    ULONG required_length                        = 0;
    HRESULT hr;

    // get info about the device
    device_info = SetupDiGetClassDevs( interfaceGuid, NULL, NULL,
                                       DIGCF_PRESENT | DIGCF_DEVICEINTERFACE );
    if ( device_info == INVALID_HANDLE_VALUE )
        return FALSE;

    // iterate until the requested instance of the interface is found
    interface_data.cbSize = sizeof( SP_DEVICE_INTERFACE_DATA );
    for ( DWORD inst = 0; inst <= instance; inst++ )
    {
        b_result = SetupDiEnumDeviceInterfaces( device_info, NULL, interfaceGuid, inst, &interface_data );

        // exit if the requested instance of the interface is not found
        if ( b_result == FALSE )
        {
            SetupDiDestroyDeviceInfoList( device_info );
            return FALSE;
        }
    }

    // Get the size of the device path.  This is supposed to fail, but it gives length of path.
    SetupDiGetDeviceInterfaceDetail( device_info, &interface_data, NULL, 0, &required_length, NULL );
    if ( GetLastError() != ERROR_INSUFFICIENT_BUFFER )
    {
        SetupDiDestroyDeviceInfoList( device_info );
        return FALSE;
    }

    // Allocate memory to store the device path.
    detail_data = (PSP_DEVICE_INTERFACE_DETAIL_DATA)
                  LocalAlloc( LMEM_FIXED, required_length );
    if ( NULL == detail_data )
    {
        SetupDiDestroyDeviceInfoList( device_info );
        return FALSE;
    }

    // get the device path
    detail_data->cbSize = sizeof( SP_DEVICE_INTERFACE_DETAIL_DATA );
    length              = required_length;
    b_result            = SetupDiGetDeviceInterfaceDetail( device_info, &interface_data,
                                                           detail_data, length, &required_length, NULL );
    if ( FALSE == b_result )
    {
        SetupDiDestroyDeviceInfoList( device_info );
        LocalFree( detail_data );
        return FALSE;
    }

    // copy the device path to the output string
    hr = StringCchCopyW( devicePath, bufLen, detail_data->DevicePath );

    // free any allocated memory
    SetupDiDestroyDeviceInfoList( device_info );
    LocalFree( detail_data );

    if ( SUCCEEDED( hr ) )
        return TRUE;
    else
        return FALSE;
} // WinusbGetDevicePath



/// Open a device with the given interface GUID and instance.
///\return Handle to the device or INVALID_HANDLE_VALUE.
HANDLE WinusbPort::WinusbOpenDevice(
    LPGUID interfaceGuid, ///< interface GUID
    DWORD  instance       ///< device instance
    )
{
    HANDLE dev_handle = NULL;
    WCHAR device_path[256];

    if ( FALSE == WinusbGetDevicePath( interfaceGuid, instance,
                                       device_path, sizeof( device_path ) ) )
        return INVALID_HANDLE_VALUE;

    dev_handle = CreateFile( device_path,
                             GENERIC_WRITE | GENERIC_READ,
                             FILE_SHARE_WRITE | FILE_SHARE_READ,
                             NULL,
                             OPEN_EXISTING,
                             FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OVERLAPPED,
                             NULL );

    if ( INVALID_HANDLE_VALUE == dev_handle )
        return INVALID_HANDLE_VALUE;

    return dev_handle;
}



/// Open the requested instance of a WINUSB device with the given USB vendor and product IDs.
///\return Error object with results of operation. Device handle is returned in handle argument.
XsError WinusbPort::WinusbOpen(
    UsbDirectionType const dir,     ///< I/O direction.
    HandleType             &rHandle ///< Extended handle for the opened device.
    )
{
    // open USB device if it hasn't been opened previously
    if ( rHandle.mDevHandle == INVALID_HANDLE_VALUE )
    {
        rHandle.mDevHandle = WinusbOpenDevice( &XsusbWinusbGuid, Instance() );
        if ( INVALID_HANDLE_VALUE == rHandle.mDevHandle )
            return XsError( MINOR_XS_ERROR, "Unable to open XSUSB device." );
    }

    // initialize WINUSB for this device if it hasn't been done previously
    if ( !WinusbClaim( rHandle ) )
    {
        WinusbClose( rHandle );
        return XsError( MINOR_XS_ERROR, "Unable to claim XSUSB device." );
    }

    // get interface descriptor with the endpoint information
    USB_INTERFACE_DESCRIPTOR iface_descriptor;
    if ( !WinUsb_QueryInterfaceSettings( rHandle.mWinusbHandle, 0, &iface_descriptor ) )
    {
        WinusbClose( rHandle );
        return XsError( MINOR_XS_ERROR, "Unable to query XSUSB interface settings." );
    }

    // get endpoint number and set the upper bit if it's a READ pipe
    rHandle.mEndpoint = Endpoint();
    if ( dir == DIR_PERIPH_TO_HOST )
        rHandle.mEndpoint |= 0x80;

    // look through the interface descriptor for the requested endpoint
    for ( int i = 0; i < iface_descriptor.bNumEndpoints; i++ )
    {
        WINUSB_PIPE_INFORMATION pipe_info;
        if ( !WinUsb_QueryPipe( rHandle.mWinusbHandle, 0, (UCHAR)i, &pipe_info ) )
        {
            WinusbClose( rHandle );
            return XsError( MINOR_XS_ERROR, "Unable to query XSUSB interface pipe." );
        }

        if ( pipe_info.PipeId == rHandle.mEndpoint )
        {
            // found the endpoint!  Return a handle that encodes the index into
            // the array of extended handles and the endpoint
            WinusbRelease( rHandle ); // Release it until the endpoint is actually needed.
            return XsError( NO_XS_ERROR );
        }
    }

    // didn't find the endpoint.
    WinusbClose( rHandle );
    return XsError( MINOR_XS_ERROR, "Unable to find requested endpoint in XSUSB device." );
} // WinusbOpen



/// Claim the opened USB device for I/O operations.
///\return An error object.
XsError WinusbPort::WinusbClaim( HandleType &rHandle ) ///< Extended handle for USB device.
{
    if ( INVALID_HANDLE_VALUE == rHandle.mDevHandle )
        return XsError( FATAL_XS_ERROR, "Trying to claim an unopened WINUSB device." );  // Can't claim a closed USB device.

    if ( INVALID_HANDLE_VALUE != rHandle.mWinusbHandle )
        return XsError( FATAL_XS_ERROR, "Trying to claim a WINUSB device that is already claimed by someone else." );  // Somebody already claimed this device.

    // Device has not been claimed yet, so try to claim it.
    if ( !WinUsb_Initialize( rHandle.mDevHandle, &rHandle.mWinusbHandle ) )
    {
        // Couldn't claim it, so return error.
        rHandle.mWinusbHandle = INVALID_HANDLE_VALUE;
        return XsError( FATAL_XS_ERROR, "Could not claim WINUSB device." );
    }

    return XsError( NO_XS_ERROR ); // Claimed it, so return "no error".
}



/// Release the opened USB device so someone else can use it.
///\return An error object.
XsError WinusbPort::WinusbRelease( HandleType &rHandle ) ///< Extended handle for USB device.
{
    if ( rHandle.mDevHandle == INVALID_HANDLE_VALUE )
    {
        if ( rHandle.mWinusbHandle == INVALID_HANDLE_VALUE )
            return XsError( NO_XS_ERROR );
        else
            return XsError( FATAL_XS_ERROR, "Open WINUSB device with invalid device handle." );
    }
    if ( rHandle.mWinusbHandle != INVALID_HANDLE_VALUE )
    {
        if ( !WinUsb_Free( ( rHandle.mWinusbHandle ) ) )
            return XsError( FATAL_XS_ERROR, "Unable to release WINUSB handle." );

        rHandle.mWinusbHandle = INVALID_HANDLE_VALUE;
    }
    return XsError( NO_XS_ERROR ); // Released it, so return "no error".
}



/// Close a device with the given handle.
///\return An error object.
XsError WinusbPort::WinusbCloseDevice( HandleType &rHandle ) ///< Extended handle for the USB device.
{
    // Already closed devices return no error by default.
    if ( ( INVALID_HANDLE_VALUE == rHandle.mDevHandle ) || ( NULL == rHandle.mDevHandle ) )
        return XsError( NO_XS_ERROR );

    // Close the device and return the result.
    if ( CloseHandle( rHandle.mDevHandle ) == FALSE )
        return XsError( FATAL_XS_ERROR, "Unable to close WINUSB device." );
    else
    {
        rHandle.mDevHandle = INVALID_HANDLE_VALUE;
        rHandle.mIsOpen    = false;
        return XsError( NO_XS_ERROR );
    }
}



/// Close the libusb device with the given extended handle.
///\return Error object.
XsError WinusbPort::WinusbClose( HandleType &rHandle ) ///< Extended handle for the USB device.
{
    XsError error;

    // Nothing to do if USB port is not open.
    if ( rHandle.mIsOpen == false )
        return error;

    error  = WinusbRelease( rHandle );
    error |= WinusbCloseDevice( rHandle );

    return XsError( NO_XS_ERROR );
}

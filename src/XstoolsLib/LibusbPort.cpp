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

#include <cassert>
#include "libusb-win32/include/usb.h" // libusb header file
#include "LibusbPort.h"



/// Set flag to false so libusb will get initialized.
bool LibusbPort::mIsLibusbInitialized = false;



/// Create a USB port object.
///\return Nothing.
LibusbPort::LibusbPort(
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
LibusbPort::~LibusbPort( void )
{
    Close();
}



/// Determine the number of instances of a USB port with this VID and PID.
///\return The number of USB ports.
unsigned int LibusbPort::GetUsbPortCount(
    VidType const vid, ///< USB vendor ID.
    PidType const pid  ///< USB product ID.
    ) const
{
    usb_find_busses();
    usb_find_devices();

    // count up the attached devices
    struct usb_bus *bus;
    struct usb_device *dev;
    unsigned dev_cnt = 0;
    for ( bus = usb_get_busses(); bus; bus = bus->next )
        for ( dev = bus->devices; dev; dev = dev->next )
            if ( ( dev->descriptor.idVendor == vid )
                 && ( dev->descriptor.idProduct == pid ) )
                dev_cnt++;

    // return the number of devices found
    return dev_cnt;
}



/// Open input and output endpoints of a USB port object.
///\return Error object.
XsError LibusbPort::Open( unsigned int const numTrials ) ///< try this number of times to open the device
{
    XsError error;

    // Open channel used to send data to the USB peripheral (if it is not already opened).
    for ( int i = numTrials; i > 0 && !mHandleToPeriph.mIsOpen; i-- )
        error = LibusbOpen( DIR_HOST_TO_PERIPH, mHandleToPeriph );

    if ( !error.IsError() )
        // Open channel used to receive data from the USB peripheral (if it is not already opened).
        for ( int i = numTrials; i > 0 && !mHandleFromPeriph.mIsOpen; i-- )
            error |= LibusbOpen( DIR_PERIPH_TO_HOST, mHandleFromPeriph );

    if ( error.IsError() )
        Close();  // Close the endpoints if an error occurred while opening them.

    return error;
}



/// Read from a USB device into a buffer.
///\return Error object.
XsError LibusbPort::Read(
    LengthType const  rqstdLength,      ///< Requested number of bytes to read.
    BufferType        &rDataFromDevice, ///< Buffer to hold data read from device.
    TimeoutType const timeoutMs         ///< Timeout in milliseconds.
    )
{
    assert( mHandleFromPeriph.mIsOpen == true );
    assert( mHandleFromPeriph.mDevHandle != NULL );
    assert( rqstdLength != 0 );
    assert( timeoutMs < 20000 );

    // Make char array for storing data read from libusb device.
    char *p_data_from_device = new char[rqstdLength];

    // Claim the interface.
    if ( usb_claim_interface( mHandleFromPeriph.mDevHandle, 0 ) < 0 )
    {
        delete [] p_data_from_device; // Delete char array.
        return XsError( FATAL_XS_ERROR, "Unable to claim libusb device interface" );
    }

    // Read data from libusb device.
    int actual_length = usb_bulk_read( mHandleFromPeriph.mDevHandle, mHandleFromPeriph.mEndpoint, p_data_from_device, rqstdLength, timeoutMs );
    assert(actual_length <= rqstdLength);

    // Release the interface.
    usb_release_interface( mHandleFromPeriph.mDevHandle, 0 );

    // Return an error if the actual number of bytes read was less than zero.
    if(actual_length < 0)
    {
        delete [] p_data_from_device; // Release the allocated storage.
        return XsError(FATAL_XS_ERROR, "Read of libusb device failed!");
    }

    // Return an error if too few bytes were read.
    if(actual_length < rqstdLength)
    {
        delete [] p_data_from_device; // Release the allocated storage.
        return XsError(FATAL_XS_ERROR, "Incomplete read of libusb device!");
    }

    // Place char data into return buffer.
    for ( int i = 0; i < actual_length; i++ )
        rDataFromDevice.push_back( *p_data_from_device++ );

    // Delete the char array.
    delete [] p_data_from_device;

    return XsError( NO_XS_ERROR );
} // Read



/// Write to a USB device from a buffer.
///\return Error object.
XsError LibusbPort::Write(
    BufferType        &rDataToDevice, ///< Buffer holding data to write to device.
    TimeoutType const timeoutMs       ///< Timeout in milliseconds.
    )
{
    assert( rDataToDevice.size() > 0 );
    assert( mHandleToPeriph.mIsOpen == true );
    assert( mHandleToPeriph.mDevHandle != NULL );
    assert( timeoutMs < 20000 );

    // Place buffer data into a char array.
    BufferType::size_type size = rDataToDevice.size();
    BufferType::size_type i;
    char *p_data_to_device     = new char[rDataToDevice.size()];
    for ( i = 0; i < size; i++ )
    {
        p_data_to_device[i] = rDataToDevice.front();
        rDataToDevice.pop_front();
    }

    // Claim the interface.
    if ( usb_claim_interface( mHandleToPeriph.mDevHandle, 0 ) < 0 )
    {
        delete [] p_data_to_device; // Delete char array.
        return XsError( FATAL_XS_ERROR, "Unable to claim libusb device interface" );
    }

    // Send char array to libusb device.
    int actual_length = usb_bulk_write( mHandleToPeriph.mDevHandle, mHandleToPeriph.mEndpoint, p_data_to_device, size, timeoutMs );

    // Release the interface.
    usb_release_interface( mHandleToPeriph.mDevHandle, 0 );

    // Return an error if the actual number of bytes sent was less than zero.
    if(actual_length < 0)
    {
        delete [] p_data_to_device; // Release the allocated storage.
        return XsError(FATAL_XS_ERROR, "Write to libusb device failed!");
    }

    // Return an error if too few bytes were written.
    if(actual_length < size)
    {
        delete [] p_data_to_device; // Release the allocated storage.
        return XsError(FATAL_XS_ERROR, "Incomplete write of libusb device!");
    }

    // Push any unsent data back into the buffer.
    for ( i = actual_length; i < size; i++ )
        rDataToDevice.push_back( p_data_to_device[i] );

    // Delete the char array.
    delete [] p_data_to_device;

    return XsError( NO_XS_ERROR );
} // Write



/// Close the input and output endpoints of a USB port object.
///\return Error object.
XsError LibusbPort::Close( void )
{
    XsError error;

    error  = LibusbClose( mHandleToPeriph );
    error |= LibusbClose( mHandleFromPeriph );
    return error;
}



/// Initialize the USB port object.
///\return Nothing.
void LibusbPort::Init( void )
{
    mHandleToPeriph.mIsOpen      = false;
    mHandleFromPeriph.mIsOpen    = false;
    mHandleToPeriph.mDevHandle   = NULL;
    mHandleFromPeriph.mDevHandle = NULL;
}



/// Initialize libusb.
///\return Nothing.
void LibusbPort::LibusbInit( void )
{
    if ( mIsLibusbInitialized == false )
    {
        usb_init();
    }
    mIsLibusbInitialized = true;
}



/// Open the requested instance of a libusb device with the given USB vendor and product IDs.
///\return Error object with results of operation. Device handle is returned in handle argument.
XsError LibusbPort::LibusbOpen(
    UsbDirectionType const dir,     ///< I/O direction.
    HandleType             &rHandle ///< Pointer to handle for the opened device.
    )
{
    // Nothing to do if USB port is already open.
    if ( rHandle.mIsOpen )
        return XsError( NO_XS_ERROR );

    usb_find_busses();
    usb_find_devices();

    struct usb_bus *p_bus;
    struct usb_device *p_dev;
    int dev_cnt = 0;

    for ( p_bus = usb_get_busses(); p_bus; p_bus = p_bus->next )
    {
        for ( p_dev = p_bus->devices; p_dev; p_dev = p_dev->next )
            if ( ( p_dev->descriptor.idVendor == Vid() )
                 && ( p_dev->descriptor.idProduct == Pid() ) )
            {
                if ( dev_cnt == Instance() )
                {
                    rHandle.mDevHandle = usb_open( p_dev );
                    if ( rHandle.mDevHandle == NULL )
                        return XsError( FATAL_XS_ERROR, "Unable to open libusb device handle" );

                    rHandle.mIsOpen    = true;
                    rHandle.mEndpoint  = Endpoint();
                    if ( dir == DIR_PERIPH_TO_HOST )
                        rHandle.mEndpoint += 0x80;
                    if ( usb_set_configuration( rHandle.mDevHandle, 1 ) < 0 )
                    {
                        usb_close( rHandle.mDevHandle );
                        rHandle.mIsOpen = false;
                        return XsError( FATAL_XS_ERROR, "Unable to set libusb device configuration" );
                    }
                    // Success - USB device was opened.
                    return XsError( NO_XS_ERROR );
                }
                dev_cnt++;
            }

    }

    return XsError( FATAL_XS_ERROR, "Unable to find libusb device VID or PID" );
} // LibusbOpen



/// Close the libusb device with the given extended handle.
///\return Error object.
XsError LibusbPort::LibusbClose( HandleType &rHandle ) ///< Extended handle for the USB device.
{
    // Nothing to do if USB port is not open.
    if ( rHandle.mIsOpen == false )
        return XsError( NO_XS_ERROR );

    // Handle is still open if result of usb_close < 0.
    rHandle.mIsOpen = usb_close( rHandle.mDevHandle ) < 0;

    if ( rHandle.mIsOpen )
        return XsError( FATAL_XS_ERROR, "Failed to close libusb device" );
    else
        return XsError( NO_XS_ERROR );  // Closed, so return "no error".
}

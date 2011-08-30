// XtractLibTest.cpp : Defines the entry point for the console application.
//

#include <iostream>
#include <string>
#include "stdafx.h"
#include "XstoolsLib.h"
#include "XstoolsApi.h"

using std::string;
using std::ostream;
using std::cerr;
using std::cout;
using std::cin;
using std::hex;
using std::endl;

#if 0
/// (Brief, one-line description of what this function does.)
///\return (Description of what is returned by this function.)
///
/// Detailed, multi-line description of this function.
/// ....
///
/// (Place '///< [in,out]' after each function parameter.)
XsError I2cInit( HostIoToMemory &i2c )
{
    int const CLK_DIVIDER = 250;
    int const PRER_LO     = 0x00;
    int const PRER_HI     = 0x01;
    int const CTR         = 0x02;
    int const ENABLE_CORE = 0x80;
    int const ENABLE_INT  = 0x40;

    i2c.Write( PRER_LO, CLK_DIVIDER & 0xFF );
    i2c.Write( PRER_HI, ( CLK_DIVIDER >> 8 ) & 0xFF );
    i2c.Write( CTR, ENABLE_CORE );

    HostIoToMemory::MemoryDataType data;
    i2c.Read( PRER_LO, data );
    cout << "PRER_LO = " << hex << data << endl;
    i2c.Read( PRER_HI, data );
    cout << "PRER_HI = " << hex << data << endl;
    i2c.Read( CTR, data );
    cout << "CTR = " << hex << data << endl;

    return XsError();
}



/// (Brief, one-line description of what this function does.)
///\return (Description of what is returned by this function.)
///
/// Detailed, multi-line description of this function.
/// ....
///
/// (Place '///< [in,out]' after each function parameter.)
XsError Tcm8240Write(
    HostIoToMemory &i2c,
    int const      addr,
    int const      data )
{
    int const TCM8240_WR_ADDR = 0x7A;
    int const TCM8240_RD_ADDR = 0x7B;
    int const TXR             = 0x03;
    int const RXR             = 0x03;
    int const CR              = 0x04;
    int const SR              = 0x04;
    int const STA             = 0x80;
    int const STO             = 0x40;
    int const RD              = 0x20;
    int const WR              = 0x10;
    int const ACK             = 0x08;
    int const IACK            = 0x01;
    int const RX_ACK          = 0x80;
    int const BUSY            = 0x40;
    int const AL              = 0x20;
    int const TIP             = 0x02;
    int const IF              = 0x01;
    HostIoToMemory::MemoryDataType status;

    i2c.Write( TXR, TCM8240_WR_ADDR );
    i2c.Write( CR, STA | WR );
    while ( true )
    {
        i2c.Read( SR, status );
        if ( !( status & TIP ) && !( status & RX_ACK ) )
            break;
    }

    i2c.Write( TXR, addr );
    i2c.Write( CR, WR );
    while ( true )
    {
        i2c.Read( SR, status );
        if ( !( status & TIP ) && !( status & RX_ACK ) )
            break;
    }

    i2c.Write( TXR, data );
    i2c.Write( CR, STO | WR );
    while ( true )
    {
        i2c.Read( SR, status );
        if ( !( status & TIP ) && !( status & RX_ACK ) )
            break;
    }

    return XsError();
} // Tcm8240Write



/// (Brief, one-line description of what this function does.)
///\return (Description of what is returned by this function.)
///
/// Detailed, multi-line description of this function.
/// ....
///
/// (Place '///< [in,out]' after each function parameter.)
XsError Tcm8240Read(
    HostIoToMemory                 &i2c,
    int const                      addr,
    HostIoToMemory::MemoryDataType &data )
{
    int const TCM8240_WR_ADDR = 0x7A;
    int const TCM8240_RD_ADDR = 0x7B;
    int const TXR             = 0x03;
    int const RXR             = 0x03;
    int const CR              = 0x04;
    int const SR              = 0x04;
    int const STA             = 0x80;
    int const STO             = 0x40;
    int const RD              = 0x20;
    int const WR              = 0x10;
    int const ACK             = 0x08;
    int const IACK            = 0x01;
    int const RX_ACK          = 0x80;
    int const BUSY            = 0x40;
    int const AL              = 0x20;
    int const TIP             = 0x02;
    int const IF              = 0x01;
    HostIoToMemory::MemoryDataType status;

    i2c.Write( TXR, TCM8240_WR_ADDR );
    i2c.Write( CR, STA | WR );
    while ( true )
    {
        i2c.Read( SR, status );
        if ( !( status & TIP ) && !( status & RX_ACK ) )
            break;
    }

    i2c.Write( TXR, addr );
    i2c.Write( CR, WR );
    while ( true )
    {
        i2c.Read( SR, status );
        if ( !( status & TIP ) && !( status & RX_ACK ) )
            break;
    }

    i2c.Write( TXR, TCM8240_RD_ADDR );
    i2c.Write( CR, STA | WR );
    while ( true )
    {
        i2c.Read( SR, status );
        if ( !( status & TIP ) && !( status & RX_ACK ) )
            break;
    }

    i2c.Write( CR, RD | ACK | STO );
    while ( true )
    {
        i2c.Read( SR, status );
        if ( !( status & TIP ) )
            break;
    }
    i2c.Read( RXR, data );

    return XsError();
} // Tcm8240Read
#endif



/// Test routine.
int _tmain(
    int    argc,
    _TCHAR *argv [] )
{
    unsigned int addrWidth, dataWidth;
    HostIoToMemory &regIo = *XsMemInit( 0, 1, addrWidth, dataWidth );
    cout << addrWidth << " " << dataWidth << endl;

    HostIoToMemory &ramIo = *XsMemInit( 0, 2, addrWidth, dataWidth );
    cout << addrWidth << " " << dataWidth << endl;

    unsigned int numInputs, numOutputs;
    HostIoToDut &dutIo = *XsDutInit( 0, 3, numInputs, numOutputs );
    cout << numInputs << " " << numOutputs << endl;

    HostIoToMemory::MemoryDataQueue wdq, rdq;
    unsigned int ramSize = 1<<addrWidth;
    rdq.clear();
#if 0
    wdq.clear();
    for ( unsigned long long j = 0; j < ramSize; j++ )
        wdq.push_back( j + 0x45 );
    ramIo.Write( 0, wdq );
    for ( unsigned int j = 0; j < wdq.size(); j++ )
        cout << "* " << hex << wdq[j] << endl;
#endif
    ramIo.Read( 0, ramSize, rdq );
    for ( unsigned int j = 0; j < rdq.size(); j++ )
        cout << rdq[j] << " ";
    cout << endl;
    exit(0);
    bool match = true;
    for ( unsigned int j = 0; j < rdq.size(); j++ )
        if ( rdq[j] != wdq[j] )
            match = false;
    if ( !match )
        cout << "Write and Read queues do not match!" << endl;
    else
        cout << "Write and read queues match!" << endl;


#if 0
    int vid, pid, instance, endpoint;

    vid      = 0x04D8;
    pid      = 0xFF8C;
    instance = 0;
    endpoint = 1;

    LibusbPort p( vid, pid, instance, endpoint );
    XsError error = p.Open();
    JtagPort jtag( &p );

    HostIoToMemory i2c( &jtag );
    i2c.UserInstr() = BitBuffer( "000010" );
    i2c.Reset();
    i2c.GetSize( 1 );
    I2cInit( i2c );

    for ( int i = 0; i < 0x20; i++ )
    {
        HostIoToMemory::MemoryDataType regValue;
        Tcm8240Read( i2c, i, regValue );
        cout << "Reg(" << hex << i << ") = " << regValue << endl;
    }
    cout << "==========================================" << endl;
    while ( !cin.eof() )
    {
        int addr;
        HostIoToMemory::MemoryDataType data;
        cin >> hex >> addr >> data;
        if(addr == 0xff)
            break;
        Tcm8240Write( i2c, addr, data );
    }
    for ( int i = 0; i < 0x20; i++ )
    {
        HostIoToMemory::MemoryDataType regValue;
        Tcm8240Read( i2c, i, regValue );
        cout << "Reg(" << hex << i << ") = " << regValue << endl;
    }
    while(true);
    exit( 0 );

    Tcm8240Write( i2c, 0x02, 0x00 );
    Tcm8240Write( i2c, 0x03, 0x17 );
    Tcm8240Write( i2c, 0x04, 0x18 );
    Tcm8240Write( i2c, 0x05, 0x80 );
    Tcm8240Write( i2c, 0xE6, 0x08 );
    Tcm8240Write( i2c, 0x0E, 0xB0 );
    Tcm8240Write( i2c, 0x11, 0x6A );
    Tcm8240Write( i2c, 0x14, 0x33 );
    for ( int i = 0; i < 0x20; i++ )
    {
        HostIoToMemory::MemoryDataType regValue;
        Tcm8240Read( i2c, i, regValue );
        cout << "Reg(" << hex << i << ") = " << regValue << endl;
    }
    while ( true )
        ;
    exit( 0 );

    while ( 1 )
    {
//        for ( int addr = 0; addr < 128; addr += 2 )
        int const TCM8240_WR_ADDR = 0x7A;
        int const TCM8240_RD_ADDR = 0x7B;
        int const TXR             = 0x03;
        int const RXR             = 0x03;
        int const CR              = 0x04;
        int const SR              = 0x04;
        int const STA             = 0x80;
        int const STO             = 0x40;
        int const RD              = 0x20;
        int const WR              = 0x10;
        int const ACK             = 0x08;
        int const IACK            = 0x01;
        int const RX_ACK          = 0x80;
        int const BUSY            = 0x40;
        int const AL              = 0x20;
        int const TIP             = 0x02;
        int const IF              = 0x01;
        HostIoToMemory::MemoryDataType status;
        int addr                  = TCM8240_WR_ADDR;
        i2c.Write( TXR, addr );
        i2c.Write( CR, STA | WR );
//            cout << "Phase 1: " << addr << endl;
        while ( true )
        {
            i2c.Read( SR, status );
            if ( !( status & TIP ) )
                break;
        }
        if ( !( status & RX_ACK ) )
            cout << "Got an ACK for address = " << addr << endl;
//            cout << "Phase 2: " << addr << endl;
//            i2c.Write( TXR, addr );
//            i2c.Write( CR, STO | WR );
//            while ( true )
//            {
//                i2c.Read( SR, status );
//                if ( !( status & TIP ) )
//                    break;
//            }
//        Tcm8240Write( i2c, 0x02, 0x00 );
//        cout << "Write\n";
//        HostIoToMemory::MemoryDataType data;
//        i2c.Write( TXR, TCM8240_WR_ADDR );
//        i2c.Write( CR, STA | WR );
//        i2c.Write( TXR, data );
//        i2c.Write( CR, STO | WR );
    }

#endif

#if 0
    for ( int i = 0; i < 0x40; i++ )
    {
        HostIoToMemory::MemoryDataType regValue;
        Tcm8240Read( i2c, i, regValue );
        cout << "Reg(" << hex << i << ") = " << regValue << endl;
    }

    while ( true )
        ;
#endif

#if 0
    HostIoToMemory rwReg( &jtag );
    rwReg.UserInstr() = BitBuffer( "000010" );
    rwReg.Reset();
    rwReg.GetSize( 12 );

    HostIoToDut rwDut( &jtag );
    rwDut.UserInstr() = BitBuffer( "000010" );
    rwDut.Reset();
    rwDut.GetSize( 14 );

    HostIoToMemory::MemoryDataQueue wdq, rdq;
    rdq.clear();
    wdq.clear();
    for ( unsigned long long j = 0; j < 11; j++ )
        wdq.push_back( j + 5 );
    rwReg.Write( 0, wdq );
    for ( unsigned int j = 0; j < wdq.size(); j++ )
        cout << "* " << hex << wdq[j] << endl;
    rwReg.Read( 0, 20, rdq );
    for ( unsigned int j = 0; j < rdq.size(); j++ )
        cout << hex << rdq[j] << endl;

    rdq.clear();
    wdq.clear();
    for ( unsigned long long j = 0; j < 50; j++ )
        wdq.push_back( j + 0x45 );
    rwMem.Write( 0, wdq );
    for ( unsigned int j = 0; j < wdq.size(); j++ )
        cout << "* " << hex << wdq[j] << endl;
    rwMem.Read( 0, 50, rdq );
    for ( unsigned int j = 0; j < rdq.size(); j++ )
        cout << hex << rdq[j] << endl;
    bool match = true;
    for ( unsigned int j = 0; j < rdq.size(); j++ )
        if ( rdq[j] != wdq[j] )
            match = false;
    if ( !match )
        cout << "Write and Read queues do not match!" << endl;

    for ( int j = 0; j < 10; j++ )
    {
        BitBuffer result;
        rwDut.Write( BitBuffer( "0" ) );
        rwDut.Read( result );
        cout << "Result: " << result << endl;
    }

    while ( 1 )
    {
        unsigned long long val;
        unsigned long long addr;
//        cin >> hex >> val;
//        error |= rwReg.Write( 0x0a, val );
//        cout << "Written Value: " << hex << val << endl;
        cin >> hex >> addr;
        rdq.clear();
        error |= rwMem.Read( addr, 16, rdq );
        cout << hex << "Read Value @ " << addr << " : " << rdq[0] << endl;
        cout << "STATUS: " << error << endl;
    }

    return 0;

    unsigned long long value;
    error |= rwReg.Read( 4, value );
    cout << "Value: " << value << endl;
    cout << "STATUS: " << error << endl;
    return 0;

    error |= jtag.ResetTap();
    error |= jtag.GoThruTapStates( RUN_TEST_IDLE, SELECT_DR_SCAN, SELECT_IR_SCAN, CAPTURE_IR, SHIFT_IR, -1 );
    BitBuffer const DUMMY( "01010101010101010101010101010101010101010101010101010101010101010101010101010101010101010"
                           "01010101010101010101010101010101010101010101010101010101010101010101010101010101010101010"
                           "01010101010101010101010101010101010101010101010101010101010101010101010101010101010101010"
                           "01010101010101010101010101010101010101010101010101010101010101010101010101010101010101010"
                           "01010101010101010101010101010101010101010101010101010101010101010101010101010101010101010"
                           "01010101010101010101010101010101010101010101010101010101010101010101010101010101010101010"
                           "01010101010101010101010101010101010101010101010101010101010101010101010101010101010101010"
                           "01010101010101010101010101010101010101010101010101010101010101010101010101010101010101010"
                           "01010101010101010101010101010101010101010101010101010101010101010101010101010101010101010"
                           "01010101010101010101010101010101010101010101010101010101010101010101010101010101010101010"
                           );
    error |= jtag.ShiftTdi( DUMMY );
    cout << "DUMMY length = " << DUMMY.size() << endl;
    BitBuffer const IDCODE_INSTR( "001001" );
    error |= jtag.ShiftTdi( IDCODE_INSTR, JtagPort::EXIT_SHIFT, JtagPort::DO_FLUSH );
    error |= jtag.GoThruTapStates( UPDATE_IR, SELECT_DR_SCAN, CAPTURE_DR, SHIFT_DR, -1 );
    BitBuffer idcode;
    error |= jtag.ShiftTdo( 32, idcode, JtagPort::EXIT_SHIFT );
    cout << "IDCODE: " << idcode << endl;
    cout << "STATUS: " << error << endl;

    error |= jtag.GoThruTapStates( UPDATE_DR, SELECT_DR_SCAN, SELECT_IR_SCAN, CAPTURE_IR, SHIFT_IR, -1 );
    error |= jtag.ShiftTdi( IDCODE_INSTR, JtagPort::EXIT_SHIFT, JtagPort::DO_FLUSH );
    error |= jtag.GoThruTapStates( UPDATE_IR, SELECT_DR_SCAN, CAPTURE_DR, SHIFT_DR, -1 );
    error |= jtag.ShiftTdo( 32, idcode, JtagPort::EXIT_SHIFT );
    cout << "IDCODE: " << idcode << endl;
    cout << "STATUS: " << error << endl;


    error |= jtag.GoThruTapStates( UPDATE_DR, SELECT_DR_SCAN, SELECT_IR_SCAN, CAPTURE_IR, SHIFT_IR, -1 );
    error |= jtag.ShiftTdi( IDCODE_INSTR, JtagPort::EXIT_SHIFT, JtagPort::DO_FLUSH );
    error |= jtag.GoThruTapStates( UPDATE_IR, SELECT_DR_SCAN, CAPTURE_DR, SHIFT_DR, -1 );
    idcode.clear();
    error |= jtag.ShiftTdo( 8 * ( 32 - 5 ), idcode, JtagPort::EXIT_SHIFT );
    cout << "CRAP: " << idcode << endl;

    if ( error.IsError() )
        cout << error << endl;
    else
        cout << "Success!" << endl;
#endif
} // _tmain

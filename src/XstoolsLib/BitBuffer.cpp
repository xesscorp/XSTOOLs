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
 *  Bit buffer FIFO object for storing streams of bits. A multi-bit word is pushed
 *  into the back of the bit buffer starting with the LSB and proceeding to the MSB.
 *  A multi-bit word is pulled from the front of the bit buffer starting with the
 *  LSB and ending with the MSB.
 *
 *  Bit buffer index:       N-1 N-2    ... 2  1  0
 *  bits go in the back --> MSB        ...      LSB --> bits come out the front
 ***********************************************************************************/

#include <cassert>   // For assert() function.
#include <algorithm> // For min() function.
#include "BitBuffer.h"


/// Default constructor.
///\return Nothing.
BitBuffer::BitBuffer( void )
{
}



/// Constructor that places the specified number of bits into the FIFO buffer, starting with LSB.
///\return Nothing.
BitBuffer::BitBuffer(
    BitsType const     val,      ///< Value from which bits are extracted.
    unsigned int const numBits ) ///< Number of bits to extract and place in buffer.
{
    assert( numBits >= 0 );
    assert( numBits <= BITS_TYPE_LENGTH );

    if ( numBits == 0 )
        return;

    BitsType word = val;
    BitsType mask = 1lu; // Start with the LSB of the value.
    // Push bits into the back of the buffer, starting with the LSB.
    for ( unsigned int i = 0; i < numBits; i++ )
    {
        deque<bool>::push_back( !!( word & mask ) ); // Push true for 1, false for 0.
        mask <<= 1;
    }

    assert( mask == ( (BitsType)1 << numBits ) );
}



/// Constructor that places the specified number of bits into the FIFO buffer, starting with LSB.
///\return Nothing.
BitBuffer::BitBuffer(
    unsigned char const * const pBits,   ///< Pointer to array of bit values.
    unsigned int const  numBits ) ///< Number of bits to extract and place in buffer.
{
    assert( numBits >= 0 );

    if ( numBits == 0 )
        return;

    // Start from index 0 and push bits into the back of the buffer.
    for ( int i = 0; i < numBits; i++ )
        deque<bool>::push_back( !!pBits[i] );  // Convert string char to true(1) or false(0).
}



/// Constructor that converts a binary string into bits pushed into the buffer, starting with right-most, LSB.
///\return Nothing.
BitBuffer::BitBuffer( string const &rString ) ///< Arbitrary-length binary string such as "1101011010".
{
    // Start from the right-end of the string (LSB) and push bits into the back of the buffer.
    for ( int i = rString.length() - 1; i >= 0; i-- )
        deque<bool>::push_back( rString[i] == '1' );  // Convert string char to true(1) or false(0).
}



/// Default destructor.
///\return Nothing.
BitBuffer::~BitBuffer( void )
{
}



/// Convert a bit buffer into a value.
///\return A value representing the bit buffer contents.
BitBuffer::operator BitsType () const
{
    assert( size() > 0 );
    assert( size() <= BITS_TYPE_LENGTH );

    BitsType word = 0;
    // Limit the number of bits to no more than are in the buffer and no more than the value can hold.
    int length    = min( size(), BITS_TYPE_LENGTH );
    // Start with the most-significant bit and proceed to the LSB at the front of the buffer.
    for ( int i = length - 1; i >= 0; i-- )
        // Shift word up and add current bit to LSB position.
        word = ( word << 1 ) | ( ( *this )[i] ? 1 : 0 );
    return word;
}



/// Convert a bit buffer into a binary string.
///\return A binary string representing the bit buffer contents.
BitBuffer::operator string () const
{
    // Start from the back of the buffer (MSB) and proceed to the front (LSB),
    // thus building the string from the left (MSB) to the right (LSB).
    string s = "";
    for ( int i = size() - 1; i >= 0; i-- )
        s += ( *this )[i] ? "1" : "0";
    return s;
}



/// Create a bit buffer from a set of bits between the first (inclusive) and last (exclusive) indices in this bit buffer.
///\return A bit buffer with the requested contents from this bit buffer.
BitBuffer BitBuffer::GetBits(
    unsigned int const first, ///< Index of first bit.
    unsigned int const last   ///< Index of last bit.
    ) const
{
    assert( first <= last );
    assert( last <= size() );

    BitBuffer result;
    for ( unsigned int i = first; i < last; i++ )
        result.push_back( ( *this )[i] );
    return result;
}



/// Read the specified number of bits from the back of the bit buffer and return them as a number.
///\return The number representing the last few bits in the bit buffer.
BitsType BitBuffer::back( unsigned int const numBits ///< Number of bits to read and form into number.
                          ) const
{
    assert( numBits > 0 );
    assert( numBits <= BITS_TYPE_LENGTH );
    assert( numBits <= size() );

    if ( numBits == 1 )
        // Return a single bit, so use inherited back() for efficiency.
        return deque<bool>::back() ? 1 : 0;  // Convert boolean into a single-bit integer value.
    else
        // Return multiple bit value, so get the bits as a bit buffer, and then convert it into a value.
        return (BitsType)GetBits( size() - numBits, size() );
}



/// Read the specified number of bits from the back of the bit buffer and return them as a binary string.
///\return The string representing the last few bits in the bit buffer.
string BitBuffer::backString( unsigned int const numBits ///< Number of bits to read and form into string.
                              ) const
{
    assert( numBits <= size() );

    if ( numBits == 1 )
        // Return a single bit, so use inherited back() for efficiency.
        return deque<bool>::back() ? "1" : "0";  // Convert boolean into a single-binary digit string.
    else
        // Return multiple bit value, so get the bits as a bit buffer, and then convert it into a string.
        return (string)GetBits( size() - numBits, size() );
}



/// Read the specified number of bits from the front of the bit buffer and return them as a number.
///\return The number representing the first few bits in the bit buffer.
BitsType BitBuffer::front( unsigned int const numBits ///< Number of bits to read and form into number.
                           ) const
{
    assert( numBits > 0 );
    assert( numBits <= BITS_TYPE_LENGTH );
    assert( numBits <= size() );

    if ( numBits == 1 )
        // Return a single bit, so use inherited front() for efficiency.
        return deque<bool>::front() ? 1 : 0;  // Convert boolean into a single-bit integer value.
    else
        // Return multiple bit value, so get the bits as a bit buffer, and then convert it into a value.
        return (BitsType)GetBits( 0, numBits );
}



/// Read the specified number of bits from the front of the bit buffer and return them as a binary string.
///\return The string representing the first few bits in the bit buffer.
string BitBuffer::frontString( unsigned int const numBits ///< Number of bits to read and form into string.
                               ) const
{
    assert( numBits <= size() );

    if ( numBits == 1 )
        // Return a single bit, so use inherited front() for efficiency.
        return deque<bool>::front() ? "1" : "0";  // Convert boolean into a single-binary digit string.
    else
        // Return multiple bit value, so get the bits as a bit buffer, and then convert it into a string.
        return (string)GetBits( 0, numBits );
}



/// Push the bits from a bit buffer into the back of this bit buffer.
///\return Nothing.
void BitBuffer::push_back( BitBuffer const &rBitBuffer2 )
{
    unsigned int length = rBitBuffer2.size();
    for ( unsigned int i = 0; i < length; i++ )
        deque<bool>::push_back( rBitBuffer2[i] );
}



/// Push the specified number of bits from the given value into the back of the bit buffer, starting with the LSB.
///\return Nothing.
void BitBuffer::push_back(
    BitsType const     val,      ///< Value from which bits are extracted.
    unsigned int const numBits ) ///< Number of bits to extract and place in buffer.
{
    if ( numBits == 1 )
        deque<bool>::push_back( !!val );  // More efficient way to handle a single bit.
    else
        push_back( BitBuffer( val, numBits ) );  // Convert value to bit buffer and concatenate it with this buffer.
}



/// Push the bits from the binary string into the back of the bit buffer, starting with the LSB.
///\return Nothing.
void BitBuffer::push_back( string const s ) ///< String from which bits are extracted.
{
    push_back( BitBuffer( s ) ); // Convert string to bit buffer and concatenate it with this buffer.
}



/// Push the bits from a bit buffer into this bit buffer.
///\return Nothing.
void BitBuffer::push_front( BitBuffer const &rBitBuffer2 )
{
    for ( int i = rBitBuffer2.size() - 1; i >= 0; i-- )
        deque<bool>::push_front( rBitBuffer2[i] );
}



/// Push the specified number of bits from the given value into the front of the bit buffer, starting with the MSB.
///\return Nothing.
void BitBuffer::push_front(
    BitsType const     val,      ///< Value from which bits are extracted.
    unsigned int const numBits ) ///< Number of bits to extract and place in buffer.
{
    if ( numBits == 1 )
        deque<bool>::push_front( !!val );  // More efficient way to handle a single bit.
    else
        push_front( BitBuffer( val, numBits ) );  // Convert value to bit buffer and add it to front of this buffer.
}



/// Push the bits from the binary string into the front of the bit buffer, starting with the MSB.
///\return Nothing.
void BitBuffer::push_front( string const s ) ///< String from which bits are extracted.
{
    push_front( BitBuffer( s ) ); // Convert string to bit buffer and add it to front of this buffer.
}



/// Remove the specified number of bits from the back of the buffer.
///\return Nothing.
void BitBuffer::pop_back( unsigned int const numBits ) ///< Number of bits to remove.
{
    assert( numBits >= 0 );
    assert( numBits <= size() );

    this->erase( end() - numBits, end() );
}



/// Remove the specified number of bits from the front of the buffer.
///\return Nothing.
void BitBuffer::pop_front( unsigned int const numBits )
{
    assert( numBits >= 0 );
    assert( numBits <= size() );

    this->erase( begin(), begin() + numBits );
}



/// Concatenate two bit buffers. The LSB of the result is the LSB of the second bit buffer.
///\return The concatenation of the bit buffers.
BitBuffer BitBuffer::operator + ( BitBuffer const &rBitBuffer2 ///< Bit buffer to concatenate to this one.
                                  ) const
{
    BitBuffer result = *this; // Load result with contents of first buffer.
    result += rBitBuffer2;    // Place contents of second buffer after the contents of the first buffer.
    return result;
}



/// Concatenate a BitBuffer onto this one.
///\return A reference to this updated BitBuffer.
BitBuffer &BitBuffer::operator += ( BitBuffer const &rBitBuffer2 ) ///< Bit buffer to concatenate to this one.
{
    push_front( rBitBuffer2 );
    return *this;
}



/// Output the contents of a bit buffer to an output stream.
///\return A reference to the output stream.
ostream &operator << (
    ostream   &os,          ///< output stream.
    BitBuffer &rBitBuffer ) ///< Bit buffer to output.
{
    os << string( rBitBuffer );
    return os;
}



using std::cerr;
using std::endl;

#define CHECK_TEST( a, b ) test_error = ( ( a ) != ( b ) );\
    cerr << ( test_error ? "Failed test " : "Passed test " ) << test_num << ":";\
    cerr << "\n\t" << ( a ) << ( test_error ? " != " : " == " ) << "\n\t" << ( b ) << endl;\
    total_error                      |= test_error;\
    test_num++;

/// Really bad BitBuffer test routine.
void BitBufferTest( void )
{
    bool test_error;
    bool total_error      = false;
    unsigned int test_num = 1;
    string test_string( "1010101010111010001011101010100111000100101001101011110110001" );
    BitsType test_val     = 0xfa51;

    BitBuffer a( test_val, 16 );
    BitsType aa           = (BitsType)a;
    CHECK_TEST( aa, test_val );

    BitBuffer b( test_val );
    BitsType bb           = (BitsType)b;
    CHECK_TEST( bb, ( test_val & 1 ) );

    BitBuffer c( test_string );
    string cc             = (string)c;
    CHECK_TEST( cc, test_string );

    string d              = test_string.substr( 0, 20 );
    CHECK_TEST( d, c.backString( 20 ) );

    string e              = test_string.substr( test_string.length() - 20, 20 );
    CHECK_TEST( e, c.frontString( 20 ) );

    BitsType f            = c.front( 20 );
    c.push_front( f, 20 );
    CHECK_TEST( f, c.front( 20 ) );
    c.pop_front( 20 );

    f = c.back( 20 );
    c.push_back( f, 20 );
    CHECK_TEST( f, c.back( 20 ) );
    c.pop_back( 20 );

    string add_string = "10101010101010101010101";
    c += BitBuffer( add_string );
    CHECK_TEST( add_string, c.frontString( add_string.length() ) );

    if ( total_error )
        cerr << endl << "FAILURE!" << endl;
    else
        cerr << endl << "Success." << endl;
} // BitBufferTest

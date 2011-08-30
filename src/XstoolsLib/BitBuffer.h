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

#ifndef BitBuffer_h
#define BitBuffer_h

#include <iostream> // For ostream.
#include <queue>    // For queues.
#include <string>   // For strings.

using std::ostream;
using std::deque;
using std::string;
using std::min;


namespace XstoolsNamespace
{
typedef unsigned long long BitsType; ///< The longest multi-bit word that can enter/exit the bit buffer.

unsigned int const BITS_TYPE_LENGTH = 8 * sizeof( BitsType ); ///< BitsType length in bits.

/// Bit buffer object for storing streams of bits.
class BitBuffer : public deque<bool>
{
public:
    /// Default constructor.
    ///\return Nothing.
    BitBuffer();

    /// Constructor that places the specified number of bits into the FIFO buffer, starting with LSB.
    ///\return Nothing.
    BitBuffer(
        BitsType const     val,           ///< Value from which bits are extracted.
        unsigned int const numBits = 1 ); ///< Number of bits to extract and place in buffer.

    /// Constructor that places the specified number of bits into the FIFO buffer, starting with LSB.
    ///\return Nothing.
    BitBuffer(
        unsigned char const * const pBits,    ///< Pointer to array of bit values.
        unsigned int const  numBits ); ///< Number of bits to extract and place in buffer.

    /// Constructor that converts a binary string into bits pushed into the buffer, starting with right-most digit.
    ///\return Nothing.
    BitBuffer( string const &rString ); ///< Arbitrary-length binary string such as "1101011010".

    /// Default destructor.
    ///\return Nothing.
    ~BitBuffer();

    /// Convert a bit buffer into a value.
    ///\return A value representing the bit buffer contents.
    operator BitsType () const;

    /// Convert a bit buffer into a binary string.
    ///\return A binary string representing the bit buffer contents.
    operator string () const;

    /// Create a bit buffer from a set of bits between the first (inclusive) and last (exclusive) indices in this bit buffer.
    ///\return A bit buffer with the requested contents from this bit buffer.
    BitBuffer GetBits(
        unsigned int const first, ///< Index of first bit.
        unsigned int const last   ///< Index of last bit.
        ) const;

    /// Read the specified number of bits from the back of the bit buffer and return them as a number.
    ///\return The number representing the last few bits in the bit buffer.
    BitsType back( unsigned int const numBits = 1 ///< Number of bits to read and form into number.
                   ) const;

    /// Read the specified number of bits from the back of the bit buffer and return them as a binary string.
    ///\return The string representing the last few bits in the bit buffer.
    string backString( unsigned int const numBits = 1 ///< Number of bits to read and form into string.
                       ) const;

    /// Read the specified number of bits from the front of the bit buffer and return them as a number.
    ///\return The number representing the first few bits in the bit buffer.
    BitsType front( unsigned int const numBits = 1 ///< Number of bits to read and form into number.
                    ) const;

    /// Read the specified number of bits from the front of the bit buffer and return them as a binary string.
    ///\return The string representing the first few bits in the bit buffer.
    string frontString( unsigned int const numBits = 1 ///< Number of bits to read and form into string.
                        ) const;

    /// Push the bits from a bit buffer into the back of this bit buffer.
    ///\return Nothing.
    void push_back( BitBuffer const &rBitBuffer2 );

    /// Push the specified number of bits from the given value into the back of the bit buffer, starting with the LSB.
    ///\return Nothing.
    void push_back(
        BitsType const     val,           ///< Value from which bits are extracted.
        unsigned int const numBits = 1 ); ///< Number of bits to extract and place in buffer.

    /// Push the bits from the binary string into the back of the bit buffer, starting with the LSB.
    ///\return Nothing.
    void push_back( string const s ); ///< String from which bits are extracted.

    /// Push the bits from a bit buffer into this bit buffer.
    ///\return Nothing.
    void push_front( BitBuffer const &rBitBuffer2 );

    /// Push the specified number of bits from the given value into the front of the bit buffer, starting with the MSB.
    ///\return Nothing.
    void push_front(
        BitsType const     val,           ///< Value from which bits are extracted.
        unsigned int const numBits = 1 ); ///< Number of bits to extract and place in buffer.

    /// Push the bits from the binary string into the front of the bit buffer, starting with the MSB.
    ///\return Nothing.
    void push_front( string const s ); ///< String from which bits are extracted.

    /// Remove the specified number of bits from the back of the buffer.
    ///\return Nothing.
    void pop_back( unsigned int const numBits = 1 ); ///< Number of bits to remove.

    /// Remove the specified number of bits from the front of the buffer.
    ///\return Nothing.
    void pop_front( unsigned int const numBits = 1 );

    /// Concatenate two bit buffers.
    ///\return The concatenation of the bit buffers.
    BitBuffer operator + ( BitBuffer const &rBitBuffer2 ///< Bit buffer to concatenate to this one.
                           ) const;

    /// Concatenate a BitBuffer onto this one.
    ///\return A reference to this updated BitBuffer.
    BitBuffer &operator += ( BitBuffer const &rBitBuffer2 ); ///< Bit buffer to concatenate to this one.

private:
};
} // XstoolsNamespace

using namespace XstoolsNamespace;


/// Output the contents of a bit buffer to an output stream.
///\return A reference to the output stream.
ostream &operator << (
    ostream   &os,           ///< output stream.
    BitBuffer &rBitBuffer ); ///< Bit buffer to output.

void BitBufferTest( void );

#endif

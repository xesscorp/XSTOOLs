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
 * Overloaded new and delete operators that detect memory corruption.
 ***********************************************************************************/

#include <iostream> // For ostreams.
#include <string>   // For endl.
#include <cstring>  // To get memset.
#include <cstdlib>  // To get calloc and free.

using std::string;
using std::ostream;
using std::cerr;
using std::endl;


// Define this if you want to check memory alloc/dealloc for corruption.
#define GUARD_THE_MEMORY

/// Allocated memory is guarded by dogtags and the size of memory like so:
/// | Dogtag | #size | .... #size bytes .... | Dogtag |
///                  ^
///                  |
///    Return void* of this address to the calling routine.

typedef unsigned int Dogtag;
static Dogtag const DOGTAG_VALUE = 0xDEADBEEF;

/// Allocate memory with dogtags added to front and back.
///\return Pointer to user-modifiable memory segment.
static void *AllocAndGuard( size_t const size )
{
    // Allocate more space than requested to hold front and back
    // dogtags and requested size of allocated memory.
    unsigned char *p_mem = (unsigned char *)calloc( 1, size + 2 * sizeof( Dogtag ) + sizeof( size_t ) );
    // Initialize front dogtag.
    *(Dogtag *)p_mem                                                  = DOGTAG_VALUE;
    // Initialize back dogtag.
    *(Dogtag *)( p_mem + sizeof( Dogtag ) + sizeof( size_t ) + size ) = DOGTAG_VALUE;
    // Initialize size.
    *(size_t *)( p_mem + sizeof( Dogtag ) )                           = size;
    // Return pointer to user-modifiable segment of allocated memory.
    return p_mem + sizeof( Dogtag ) + sizeof( size_t );
}



/// Test dogtag values and then deallocate memory.
static void TestAndDealloc( void *p )
{
    // Point to the actual start of the allocated memory.
    unsigned char *p_mem = (unsigned char *)p - sizeof( size_t ) - sizeof( Dogtag );
    // Get the size of the user-modifiable segment.
    size_t size          = *(size_t *)( p_mem + sizeof( Dogtag ) );
    // Check the front dogtag.
    if ( *(Dogtag *)p_mem != DOGTAG_VALUE )
    {
        ;
    }
    // Check the back dogtag.
    else if ( *(Dogtag *)( p_mem + sizeof( Dogtag ) + sizeof( size_t ) + size ) != DOGTAG_VALUE )
    {
        ;
    }
    else
    {
        // Clear the allocated memory.
        memset( (void*)p_mem, 0, size + 2 * sizeof( Dogtag ) + sizeof( size_t ) );
        // Deallocate the memory.
        free( (void *)p_mem );
    }
}



/// Overload the default new operator.
///\return Pointer to allocated storage.
void *operator new ( size_t const size ) ///< # of bytes to allocate.
{
#ifdef GUARD_THE_MEMORY
    return AllocAndGuard( size );

#else
    return calloc( 1, size );

#endif
}



// Overload the default new array operator.
///\return Pointer to allocated storage.
void *operator new [] ( size_t const size ) ///< # of bytes to allocate.
{
#ifdef GUARD_THE_MEMORY
    return AllocAndGuard( size );

#else
    return calloc( 1, size );

#endif
}



// Overload the default delete operator.
void operator delete ( void *p ) ///< Pointer to space to be deallocated.
{
#ifdef GUARD_THE_MEMORY
    return TestAndDealloc( p );

#else
    free( p );
#endif
}



// Overload the default delete array operator.
void operator delete [] ( void *p ) ///< Pointer to space to be deallocated.
{
#ifdef GUARD_THE_MEMORY
    return TestAndDealloc( p );

#else
    free( p );
#endif
}

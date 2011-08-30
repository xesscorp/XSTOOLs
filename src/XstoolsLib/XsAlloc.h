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

#ifndef XsAlloc_h
#define XsAlloc_h

namespace XstoolsNamespace
{
/// Overload the default new operator.
///\return Pointer to allocated storage.
void *operator new ( size_t const size ); ///< # of bytes to allocate.

// Overload the default new array operator.
///\return Pointer to allocated storage.
void *operator new [] ( size_t const size ); ///< # of bytes to allocate.

// Overload the default delete operator.
void operator delete ( void *p ); ///< Pointer to space to be deallocated.

// Overload the default delete array operator.
void operator delete [] ( void *p ); ///< Pointer to space to be deallocated.
} // XstoolsNamespace

using namespace XstoolsNamespace;

#endif

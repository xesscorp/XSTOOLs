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
 * Provides an object for recording and reporting errors with a consistent format.
 *
 * The severity of the error is also indicated. If the severity
 * is high enough, the object will terminate the entire program. Otherwise,
 * the object will record the number of errors that occurred.
 * Later, the calling program can query whether an error occurred and
 * decide what action to take.
 *
 * This object also stores error messages and displays them in a Windows
 * message window or as text in a command-line environment.
 ***********************************************************************************/

#ifndef XsError_h
#define XsError_h

#include <iostream> ///< For ostream objects.
#include <string>   ///< For string objects.

using std::ostream;
using std::cerr;
using std::endl;
using std::string;


namespace XstoolsNamespace
{
typedef  string ErrorMsgType;
typedef enum
{
    NO_XS_ERROR    = 0, ///< No error. (Must be zero for boolean test.)
    MINOR_XS_ERROR = 1, ///< minor error (no abort)
    MAJOR_XS_ERROR = 2, ///< major error (no abort)
    FATAL_XS_ERROR = 3  ///< fatal error (causes abort)
} ErrorSeverityType;    ///< Error severity levels.

/// Provides an object for recording and reporting errors with a consistent format.
class XsError
{
public:
    XsError(
        ErrorSeverityType const severity = NO_XS_ERROR, ///< Severity of error.
        ErrorMsgType const      &msg = ""               ///< Error message.
        );

    /// Error object type converter returns error severity.
    ///\return Error severity.
    operator ErrorSeverityType () const;

    /// Error object type converter returns error message string.
    ///\return Error message string.
    operator ErrorMsgType () const;

    /// Set the severity of the error object.
    ///\return Error object.
    XsError &operator = ( ErrorSeverityType const errorSeverity ); ///< Severity of the error.

    /// Set the message of the error object.
    ///\return Error object.
    XsError &operator = ( ErrorMsgType const &rErrorMsg ); ///< New error message.

    /// Calculate the OR of two error objects.
    ///\return An error object that is the OR of the two error object operands.
    XsError operator | ( XsError const &rXsError ///< 2nd operand.
                         ) const;

    /// Calculate the OR of two error objects.
    ///\return An error object that is the OR of the two error object operands.
    XsError &operator |= ( XsError const &rXsError ); ///< 2nd operand.

    /// Append a string to the message in this error object.
    ///\return A new error object with the concatenated message.
    XsError operator + ( ErrorMsgType const &s ///< String to concatenate to error message.
                         ) const;

    /// Append a string to the message in this error object.
    ///\return The original error object with the concatenated message.
    XsError &operator += ( ErrorMsgType const &s ); ///< String to concatenate to error message.

    /// Append a char string to the message in this error object.
    ///\return A new error object with the concatenated message.
    XsError operator + ( char const *pCharString ///< String to concatenate to error message.
                         ) const;

    /// Append a char string to the message in this error object.
    ///\return The original error object with the concatenated message.
    XsError &operator += ( char const *pCharString ); ///< String to concatenate to error message.

    /// Determine if an error has been recorded.
    ///\return True if any error has been recorded.
    bool IsError( void ) const;

    /// Set error severity and do something appropriate.
    ///\return Nothing.
    void Severity( ErrorSeverityType severity ); ///< Error severity being assigned to object.

    /// Get error severity.
    ///\return Reference to severity member.
    ErrorSeverityType Severity( void ) const;

private:
    /// States of the error object.
    typedef enum
    {
        STATE_INITIAL,    ///< Just starting error message
        STATE_IN_MESSAGE, ///< Currently printing error message
    } XsErrorState;

    static const int ABORT_THRESHOLD = 1; ///< # of errors allowed before program is aborted.

    ErrorSeverityType mSeverity; ///< Severity of error.
    ErrorMsgType mMsg;           ///< Error message.
    unsigned int mNumErrors;     ///< # of errors that have been recorded.
};
} // XstoolsNamespace

using namespace XstoolsNamespace;

/// Output an error object to a stream.
///\return A reference to the output stream.
ostream &operator << (
    ostream       &os,      ///< Output stream.
    XsError const &rXsError ///< Error object that outputs message.
    );

#endif

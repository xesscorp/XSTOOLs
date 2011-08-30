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


#include <cassert> ///< For assertions.


#include "xserror.h" ///< For error object declarations.


#define ERRLOC __FILE__( __LINE__ )


/// Construct an error object.
///\return Nothing.
XsError::XsError(
    ErrorSeverityType const severity, ///< Severity of error.
    ErrorMsgType const      &rMsg     ///< Error message.
    )
{
    Severity( severity );
    mMsg       = rMsg;
    mNumErrors = 0;
}



/// Error object type converter returns error severity.
///\return Error severity.
XsError::operator ErrorSeverityType () const
{
    return XsError::Severity();
}



/// Error object type converter returns error message string.
///\return Error message string.
XsError::operator ErrorMsgType () const
{
    return mMsg;
}



/// Set the severity of the error object.
///\return Error object.
XsError &XsError::operator = ( ErrorSeverityType const errorSeverity ) ///< Severity of the error.
{
    Severity( errorSeverity );
    return *this;
}



/// Set the message of the error object.
///\return Error object.
XsError &XsError::operator = ( ErrorMsgType const &rErrorMsg ) ///< New error message.
{
    mMsg = rErrorMsg;
    return *this;
}



#define MAX( a, b ) ( ( a ) > ( b ) ? ( a ) : ( b ) )

/// Calculate the OR of two error objects.
///\return An error object that is the OR of the two error object operands.
XsError XsError::operator | ( XsError const &rXsError ///< 2nd operand.
                              ) const
{
    XsError or_error = *this;
    return or_error |= rXsError;
}



/// Calculate the OR of two error objects.
///\return An error object that is the OR of the two error object operands.
XsError &XsError::operator |= ( XsError const &rXsError ) ///< 2nd operand.
{
    // Concatenate the error messages.
    if ( IsError() && rXsError.IsError() )
        *this += "\n- AND -\n";
    if ( rXsError.IsError() )
        *this += (ErrorMsgType)rXsError;

    // Severity of the combined errors is the largest severity.
    Severity( MAX( Severity(), rXsError.Severity() ) );

    return *this;
}



/// Append a string to the message in this error object.
///\return A new error object with the concatenated message.
XsError XsError::operator + ( ErrorMsgType const &s ///< String to concatenate to error message.
                              ) const
{
    // Return new error object with concatenated error message strings.
    return XsError( Severity(), this->mMsg + s );
}



/// Append a string to the message in this error object.
///\return The original error object with the concatenated message.
XsError &XsError::operator += ( ErrorMsgType const &s ) ///< String to concatenate to error message.
{
    mMsg += s;
    return *this;
}



/// Append a char string to the message in this error object.
///\return A new error object with the concatenated message.
XsError XsError::operator + ( char const *pCharString ///< String to concatenate to error message.
                              ) const
{
    return XsError( Severity(), mMsg + ErrorMsgType( pCharString ) );
}



/// Append a char string to the message in this error object.
///\return The original error object with the concatenated message.
XsError &XsError::operator += ( char const *pCharString ) ///< String to concatenate to error message.
{
    mMsg += ErrorMsgType( pCharString );
    return *this;
}



/// Determine if an error has been recorded.
///\return True if any error has been recorded.
bool XsError::IsError( void ) const
{
    return Severity() == NO_XS_ERROR ? false : true;
}



/// Set error severity and do something appropriate.
///\return Nothing.
void XsError::Severity( ErrorSeverityType severity ) ///< Error severity being assigned to object.
{
    mSeverity = severity;
    switch ( mSeverity )
    {
        case NO_XS_ERROR:
            break;

        case MINOR_XS_ERROR:
            break;

        case MAJOR_XS_ERROR:
            break;

        case FATAL_XS_ERROR:
            cerr << *this;
            abort();
    }
}



/// Get error severity.
///\return Reference to severity member.
ErrorSeverityType XsError::Severity( void ) const
{
    return mSeverity;
}



/// Output an error object to a stream.
///\return A reference to the output stream.
ostream &operator << (
    ostream       &os,      ///< Output stream.
    XsError const &rXsError ///< Error object that outputs message.
    )
{
    os << "Severity: " << (ErrorSeverityType)rXsError << "\n" << (ErrorMsgType)rXsError;
    return os;
}



#if 0

/// Create an error object with output going to a stream.
XSError::XSError( ostream &s )
{
    Setup( s );
}



/// Initialize an error object.
void XSError::Setup( ostream &s )
{
    for ( XSErrorSeverity i = XSErrorMin; i < XSErrorMax; i = (XSErrorSeverity)( (int)i + 1 ) )
        SetNumErrors( i, 0 );
    os        = &s;
    state     = XSErrorInitial;
    severity  = XSErrorNone;
    header    = "";
    storedMsg = "";
    batch     = false;
}



/// Destroy error object.
XSError::~XSError( void )
{
}



/// Assign contents of one source error object to another.
///\return reference to the object whose contents were overwritten.
XSError &XSError::operator = ( XSError &src ) ///< overwrite the error object with the contents of this one
{
    for ( XSErrorSeverity i = XSErrorMin; i < XSErrorMax; i = (XSErrorSeverity)( (int)i + 1 ) )
        SetNumErrors( i, src.GetNumErrors( i ) );
    os        = src.os;
    state     = src.state;
    severity  = src.severity;
    header    = src.header;
    storedMsg = src.storedMsg;
    batch     = src.batch;
    return *this;
}



/// Get number of errors of a certain severity that have occurred.
///\return the number of errors of severity s
unsigned int XSError::GetNumErrors( XSErrorSeverity s /**< severity */ ) const
{
    assert( s >= XSErrorMin && s < XSErrorMax );
    return numErrors[s];
}



/// Set number of errors of a certain type that have occurred.
void XSError::SetNumErrors(
    XSErrorSeverity s,  ///< error severity level
    unsigned int    n ) ///< set number of errors of severity s to this
{
    assert( s >= XSErrorMin && s < XSErrorMax );
    numErrors[s] = n;
}



/// Returns true if any errors were recorded by this error object.
///\return true if errors were reported by this object, false otherwise
bool XSError::IsError( void ) const
{
    for ( XSErrorSeverity i = XSErrorMin; i < XSErrorMax; i = (XSErrorSeverity)( (int)i + 1 ) )
        if ( GetNumErrors( i ) )
            return true;

    // yes, there were errors
    return false; // no errors were recorded
}



/// Return the severity of the current error message.
///\return severity of current error message
XSErrorSeverity XSError::GetSeverity( void ) const
{
    return severity;
}



/// Set severity of next error message.
void XSError::SetSeverity( XSErrorSeverity s ) ///< error severity level
{
    severity = s;
    switch ( severity )
    {
        case XSErrorFatal:
            *os << GetHeader().c_str() << " FATAL ERROR: ";
            SetState( XSErrorInMessage );
            break;

        case XSErrorMajor:
            *os << GetHeader().c_str() << " MAJOR ERROR: ";
            os->flush();
            SetState( XSErrorInMessage );
            break;

        case XSErrorMinor:
            *os << GetHeader().c_str() << " MINOR ERROR: ";
            os->flush();
            SetState( XSErrorInMessage );
            break;

        case XSErrorNone:
            *os << GetHeader().c_str() << ": ";
            os->flush();
            SetState( XSErrorInMessage );
            break;

        default:
            SetSeverity( XSErrorMinor );
            *os << "\nerror severity was incorrectly set!\n";
            os->flush();
            EndMsg();
            break;
    } // switch
}     // SetSeverity



/// Get the current state of the error object.
///\return the current state of the error object
XSErrorState XSError::GetState( void ) const
{
    return state;
}



/// Set the state of the error object
void XSError::SetState( XSErrorState s ) ///< desired state of error object
{
    state = s;
}



/// Set header string for each error message.
void XSError::SetHeader( string &h ) ///< string containing error message header
{
    header = h;
}



/// Get the current error message header.
///\return reference to error message header string
string &XSError::GetHeader( void )
{
    return header;
}



/// Enable batch processing (i.e., disable error messages).
void XSError::EnableBatch( bool b ) ///< if true, messages are disabled for batch processing
{
    batch = b; // disable user prompts (i.e. enable batch processing) when true
}



/// End the current error message and clean-up for the next one.
void XSError::EndMsg( void )
{
    cerr << storedMsg;
    switch ( GetSeverity() )
    {
        case XSErrorFatal:
            SetNumErrors( XSErrorFatal, GetNumErrors( XSErrorFatal ) + 1 );
            *os << ( "Abnormal termination of program\n" );
#ifdef _WINDOWS
            if ( !batch )
                AfxMessageBox( storedMsg.c_str(), MB_ICONSTOP );
#endif
            exit( 1 );
            break;

        case XSErrorMajor:
            SetNumErrors( XSErrorMajor, GetNumErrors( XSErrorMajor ) + 1 );
#ifdef _WINDOWS
            if ( !batch )
                AfxMessageBox( storedMsg.c_str(), MB_ICONEXCLAMATION );
#endif
            storedMsg = "";
            SetState( XSErrorInitial );
            break;

        case XSErrorMinor:
            SetNumErrors( XSErrorMinor, GetNumErrors( XSErrorMinor ) + 1 );
#ifdef _WINDOWS
            if ( !batch )
                AfxMessageBox( storedMsg.c_str(), MB_ICONEXCLAMATION );
#endif
            storedMsg = "";
            SetState( XSErrorInitial );
            break;

        case XSErrorNone:
            SetNumErrors( XSErrorNone, GetNumErrors( XSErrorNone ) + 1 );
#ifdef _WINDOWS
            if ( !batch )
                AfxMessageBox( storedMsg.c_str(), MB_ICONINFORMATION );
#endif
            storedMsg = "";
            SetState( XSErrorInitial );
            break;

        default:
            SetSeverity( XSErrorMinor );
            *os << "\nerror severity was not set!\n";
            os->flush();
#ifdef _WINDOWS
            if ( !batch )
                AfxMessageBox( storedMsg.c_str(), MB_ICONINFORMATION );
#endif
            storedMsg = "";
            SetState( XSErrorInitial );
            break;
    } // switch
}     // EndMsg



/// A simple, one-step method for sending an error message.
void XSError::SimpleMsg(
    XSErrorSeverity s,     ///< severity of this error
    string          &msg ) ///< error message
{
    SetSeverity( s );
    storedMsg = storedMsg + msg;
    *os << msg.c_str();
    EndMsg();
}



/// A simple, one-step method for sending an error message.
void XSError::SimpleMsg(
    XSErrorSeverity s,     ///< severity of this error
    char            *msg ) ///< error message
{
    SetSeverity( s );
    storedMsg = storedMsg + (string)msg;
    *os << msg;
    EndMsg();
}



/// Overload << operator to concatenate an integer to an error message.
///\return reference to the error object
XSError &XSError::operator << ( long n ) ///< integer to concatenate to error message
{
    char num[30];
    sprintf( num, "%ld", n );
    storedMsg = storedMsg + (string)num;
    *os << num;
    return *this;
}



/// Overload << operator to concatenate a float to an error message.
///\return reference to the error object
XSError &XSError::operator << ( float f ) ///< float to concatenate to error message
{
    char num[30];
    sprintf( num, "%f", f );
    storedMsg = storedMsg + (string)num;
    *os << num;
    return *this;
}



/// Overload << operator to concatenate a character string to an error message.
///\return reference to the error object
XSError &XSError::operator << ( char *msg ) ///< char. string to concatenate to error message
{
    storedMsg = storedMsg + (string)msg;
    *os << msg;
    return *this;
}



/*
  * /// Overload << operator to concatenate a string to an error message.
  * ///\return reference to the error object
  * XSError& XSError::operator<<(string& msg)	///< string to concatenate to error message
  * {
  *  storedMsg = storedMsg + msg;
  * *os << msg.c_str();
  *  return *this;
  * }
  */

/// Overload << operator to concatenate a string to an error message.
///\return reference to the error object
XSError &XSError::operator << ( string msg ) ///< string to concatenate to error message
{
    storedMsg = storedMsg + msg;
    *os << msg.c_str();
    return *this;
}



/// Overload << operator to set the output channel for the error object.
///\return reference to the error object
XSError &XSError::operator << ( ostream &s ) ///< output stream where error messages will be directed
{
    *os << s;
    return *this;
}



#endif

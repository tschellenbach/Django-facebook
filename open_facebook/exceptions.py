
'''
Facebook error classes also see
http://fbdevwiki.com/wiki/Error_codes#User_Permission_Errors
'''
import ssl
import urllib2


class OpenFacebookException(Exception):

    '''
    BaseClass for all open facebook errors
    '''

    @classmethod
    def codes_list(cls):
        '''
        Returns the codes as a list of instructions
        '''
        if hasattr(cls, 'codes'):
            codes_list = [cls.codes]
            if isinstance(cls.codes, list):
                codes_list = cls.codes
            return codes_list

    @classmethod
    def range(cls):
        '''
        Returns for how many codes this Exception, matches with the eventual
        goal of matching an error to the most specific error class
        '''
        range = 0
        codes_list = cls.codes_list()
        for c in codes_list:
            if isinstance(c, tuple):
                start, stop = c
                range += stop - start + 1
            else:
                range += 1

        # make sure none specific exceptions are last in the order
        if not range:
            range = 1000

        return range


class ParameterException(OpenFacebookException):

    '''
    100-189
    190 and up are oauth errors
    '''
    codes = (100, 189)


class UnknownException(OpenFacebookException):

    '''
    Raised when facebook themselves don't know what went wrong
    '''
    codes = 1


class OAuthException(OpenFacebookException):
    pass


class PermissionException(OAuthException):

    '''
    200-300
    '''
    codes = [3, (200, 299)]


class UserPermissionException(PermissionException):
    codes = (300, 399)


class FeedActionLimit(UserPermissionException):

    '''
    When you posted too many times from one user acount
    '''
    codes = 341


class OpenGraphException(OpenFacebookException):

    '''
    Raised when we get error 3502, representing a problem with facebook
    open graph data on the page
    '''
    codes = 3502


class DuplicateStatusMessage(OpenFacebookException):
    codes = 506


class MissingParameter(OpenFacebookException):
    pass


class AliasException(OpenFacebookException):

    '''
    When you send a request to a non existant url facebook gives this error
    instead of a 404....
    '''
    codes = 803


class UnsupportedDeleteRequest(OpenFacebookException):
    pass


class ParseException(OpenFacebookException):

    '''
    Anything preventing us from parsing the Facebook response
    '''
    pass


class FacebookUnreachable(OpenFacebookException):

    '''
    Timeouts, 500s, SSL errors etc
    '''
    pass


class FacebookSSLError(FacebookUnreachable, ssl.SSLError):
    pass


class FacebookHTTPError(FacebookUnreachable, urllib2.HTTPError):
    pass


class FacebookURLError(FacebookUnreachable, urllib2.URLError):
    pass


def map_unreachable_exception(e):
    '''
    We always raise the original and new subclass to
     - preserve backwards compatibility
    '''
    exception_class = FacebookUnreachable
    if isinstance(e, ssl.SSLError):
        exception_class = FacebookSSLError
    elif isinstance(e, urllib2.HTTPError):
        exception_class = FacebookHTTPError
    elif isinstance(e, urllib2.URLError):
        exception_class = FacebookURLError
    return exception_class


def convert_unreachable_exception(e, error_format='Facebook is unreachable %s'):
    '''
    Converts an SSLError, HTTPError or URLError into something subclassing
    FacebookUnreachable allowing code to easily try except this
    '''
    exception_class = map_unreachable_exception(e)
    error_message = error_format % e.message
    exception = exception_class(error_message)
    return exception


def get_exception_classes():
    from open_facebook import exceptions as facebook_exceptions
    all_exceptions = dir(facebook_exceptions)
    classes = [getattr(facebook_exceptions, e, None) for e in all_exceptions]
    exception_classes = [e for e in classes if getattr(
                         e, 'codes', None) and issubclass(
                         e, OpenFacebookException)]
    return exception_classes

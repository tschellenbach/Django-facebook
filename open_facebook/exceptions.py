


class OpenFacebookException(Exception):
    pass

class UnknownException(OpenFacebookException):
    '''
    Raised when facebook themselves don't know what went wrong
    '''
    pass

class OAuthException(OpenFacebookException):
    pass 

class PermissionException(OAuthException):
    pass

class FeedActionLimit(OAuthException):
    '''
    When you posted too many times from one user acount
    '''
    pass

class DuplicateStatusMessage(OpenFacebookException):
    pass

class MissingParameter(OpenFacebookException):
    pass

class AliasException(OpenFacebookException):
    '''
    When you send a request to a non existant url facebook gives this error
    instead of a 404....
    '''
    pass
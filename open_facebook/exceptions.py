


class OpenFacebookException(Exception):
    pass

class OAuthException(OpenFacebookException):
    pass 

class PermissionException(OAuthException):
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
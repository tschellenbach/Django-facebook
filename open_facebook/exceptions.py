
'''
Facebook error classes also see
http://fbdevwiki.com/wiki/Error_codes#User_Permission_Errors
'''

class OpenFacebookException(Exception):
    '''
    BaseClass for all errors
    
    '''
    pass



class ParameterException(OpenFacebookException):
    '''
    100-200
    '''
    codes = (100,200)

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
    codes = (200,299)
    
    
class UserPermissionException(PermissionException):
    codes = (300,399)






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
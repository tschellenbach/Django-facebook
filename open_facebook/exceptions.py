
'''
Facebook error classes also see
http://fbdevwiki.com/wiki/Error_codes#User_Permission_Errors
'''


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

        #make sure none specific exceptions are last in the order
        if not range:
            range = 1000

        return range


class ParameterException(OpenFacebookException):
    '''
    100-200
    '''
    codes = (100, 199)


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

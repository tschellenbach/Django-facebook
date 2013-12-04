class FacebookException(Exception):

    '''
    Base class for Facebook related exceptions
    '''
    pass


class IncompleteProfileError(FacebookException):

    '''
    Raised when we get insufficient data to create a profile for a user.
    One example is a Facebook token, without permissions to see the email.
    '''
    pass


class AlreadyConnectedError(FacebookException):

    '''
    Raised when another user account is already connected to your Facebook id
    '''

    def __init__(self, users):
        self.users = users


class AlreadyRegistered(FacebookException):

    '''
    Raised if you try to register when there's already an account with
    the given email or facebook id
    '''
    pass


class MissingPermissionsError(FacebookException):

    '''
    Raised if we lack permissions
    '''
    pass

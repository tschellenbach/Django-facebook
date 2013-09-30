class FacebookException(Exception):
    pass


class IncompleteProfileError(FacebookException):
    pass


class AlreadyConnectedError(FacebookException):

    def __init__(self, users):
        self.users = users


class AlreadyRegistered(FacebookException):
    pass


class MissingPermissionsError(FacebookException):
    pass

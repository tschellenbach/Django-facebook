


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
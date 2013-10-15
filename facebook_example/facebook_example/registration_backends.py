'''
Here a demo of how you can customize the registration backends
'''
from registration.backends.default.views import RegistrationView
from django_facebook.registration_backends import NooptRegistrationBackend


class DjangoRegistrationDefaultBackend(RegistrationView, NooptRegistrationBackend):
    '''
    The redirect behaviour will still be controlled by the
        post_error
        post_connect
    functions
    the form and other settings will be taken from the default backend
    '''
    pass

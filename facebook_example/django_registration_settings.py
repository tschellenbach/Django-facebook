from facebook_example.settings import *


MODE = 'django_registration'

FACEBOOK_REGISTRATION_BACKEND = 'registration.backends.default.DefaultBackend'


INSTALLED_APPS += (
    'registration',
)

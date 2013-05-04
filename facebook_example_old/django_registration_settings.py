from facebook_example.settings import *


MODE = 'django_registration'

FACEBOOK_REGISTRATION_BACKEND = 'registration_backends.DjangoRegistrationDefaultBackend'


INSTALLED_APPS += (
    'registration',
)

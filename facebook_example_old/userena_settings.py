from facebook_example.settings import *

MODE = 'userena'

FACEBOOK_REGISTRATION_BACKEND = 'django_facebook.registration_backends.UserenaBackend'


'''
Settings based on these docs
http://docs.django-userena.org/en/latest/installation.html#installing-django-userena
'''

AUTHENTICATION_BACKENDS = (
    'django_facebook.auth_backends.FacebookBackend',
    'userena.backends.UserenaAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
)


EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

LOGIN_REDIRECT_URL = '/accounts/%(username)s/'
LOGIN_URL = '/accounts/signin/'
LOGOUT_URL = '/accounts/signout/'
ANONYMOUS_USER_ID = 1

INSTALLED_APPS += (
    'userena',
    'guardian',
)

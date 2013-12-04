from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# : Your facebook app id
FACEBOOK_APP_ID = getattr(settings, 'FACEBOOK_APP_ID', None)
# : Your facebook app secret
FACEBOOK_APP_SECRET = getattr(settings, 'FACEBOOK_APP_SECRET', None)
# : The default scope we should use, note that registration will break without email
FACEBOOK_DEFAULT_SCOPE = getattr(settings, 'FACEBOOK_DEFAULT_SCOPE', [
    'email', 'user_about_me', 'user_birthday', 'user_website'])

# : If we should store likes
FACEBOOK_STORE_LIKES = getattr(settings, 'FACEBOOK_STORE_LIKES', False)
# : If we should store friends
FACEBOOK_STORE_FRIENDS = getattr(settings, 'FACEBOOK_STORE_FRIENDS', False)

# : If we should be using celery to store friends and likes (recommended)
FACEBOOK_CELERY_STORE = getattr(settings, 'FACEBOOK_CELERY_STORE', False)
# : Use celery for updating tokens, recommended since it's quite slow
FACEBOOK_CELERY_TOKEN_EXTEND = getattr(
    settings, 'FACEBOOK_CELERY_TOKEN_EXTEND', False)

default_registration_backend = 'django_facebook.registration_backends.FacebookRegistrationBackend'
# : Allows you to overwrite the registration backend
# : Specify a full path to a class (defaults to django_facebook.registration_backends.FacebookRegistrationBackend)
FACEBOOK_REGISTRATION_BACKEND = getattr(
    settings, 'FACEBOOK_REGISTRATION_BACKEND', default_registration_backend)

# Absolute canvas page url as per facebook standard
FACEBOOK_CANVAS_PAGE = getattr(settings, 'FACEBOOK_CANVAS_PAGE',
                               'http://apps.facebook.com/django_facebook_test/')

# Disable this setting if you don't want to store a local image
FACEBOOK_STORE_LOCAL_IMAGE = getattr(
    settings, 'FACEBOOK_STORE_LOCAL_IMAGE', True)

# Track all raw data coming in from FB
FACEBOOK_TRACK_RAW_DATA = getattr(settings, 'FACEBOOK_TRACK_RAW_DATA', False)


FACEBOOK_DEBUG_REDIRECTS = getattr(settings, 'FACEBOOK_DEBUG_REDIRECTS', False)

# READ only mode, convenient when doing load testing etc.
FACEBOOK_READ_ONLY = getattr(settings, 'FACEBOOK_READ_ONLY', False)

# Allow custom registration template
default_registration_template = [
    'django_facebook/registration.html', 'registration/registration_form.html']
FACEBOOK_REGISTRATION_TEMPLATE = getattr(settings,
                                         'FACEBOOK_REGISTRATION_TEMPLATE', default_registration_template)

# Allow custom signup form
FACEBOOK_REGISTRATION_FORM = getattr(settings,
                                     'FACEBOOK_REGISTRATION_FORM', None)


# Fall back redirect location when no other location was found
FACEBOOK_LOGIN_DEFAULT_REDIRECT = getattr(
    settings, 'FACEBOOK_LOGIN_DEFAULT_REDIRECT', '/')

# Force profile update every login
FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN = getattr(
    settings, 'FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN', False)


# Retry an open graph share 6 times (once every 15 minutes)
FACEBOOK_OG_SHARE_RETRIES = getattr(settings, 'FACEBOOK_OG_SHARE_RETRIES', 6)
# Retry a failed open graph share (when we have an updated token) for this
# number of days
FACEBOOK_OG_SHARE_RETRY_DAYS = getattr(
    settings, 'FACEBOOK_OG_SHARE_RETRY_DAYS', 7)
FACEBOOK_OG_SHARE_DB_TABLE = getattr(
    settings, 'FACEBOOK_OG_SHARE_DB_TABLE', None)


# Force profile update every login
FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN = getattr(
    settings, 'FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN', False)

# Profile image location
FACEBOOK_PROFILE_IMAGE_PATH = getattr(
    settings, 'FACEBOOK_PROFILE_IMAGE_PATH', None)

# Ability to easily overwrite classes used for certain tasks
FACEBOOK_CLASS_MAPPING = getattr(
    settings, 'FACEBOOK_CLASS_MAPPING', None)

FACEBOOK_SKIP_VALIDATE = getattr(
    settings, 'FACEBOOK_SKIP_VALIDATE', False)

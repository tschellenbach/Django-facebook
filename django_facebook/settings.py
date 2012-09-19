from django.conf import settings


# these 3 should be provided by your app
FACEBOOK_APP_ID = getattr(settings, 'FACEBOOK_APP_ID', None)
FACEBOOK_APP_SECRET = getattr(settings, 'FACEBOOK_APP_SECRET', None)
FACEBOOK_DEFAULT_SCOPE = getattr(settings, 'FACEBOOK_DEFAULT_SCOPE', [
    'email', 'user_about_me', 'user_birthday', 'user_website'])

# Absolute canvas page url as per facebook standard
FACEBOOK_CANVAS_PAGE = getattr(settings, 'FACEBOOK_CANVAS_PAGE',
                               'http://apps.facebook.com/fashiolista_test/')

# Disable this setting if you don't want to store a local image
FACEBOOK_STORE_LOCAL_IMAGE = getattr(
    settings, 'FACEBOOK_STORE_LOCAL_IMAGE', True)

# These you don't need to change
FACEBOOK_HIDE_CONNECT_TEST = getattr(settings,
                                     'FACEBOOK_HIDE_CONNECT_TEST', False)
# Track all raw data coming in from FB
FACEBOOK_TRACK_RAW_DATA = getattr(settings, 'FACEBOOK_TRACK_RAW_DATA', False)

# if we should store friends and likes
FACEBOOK_STORE_LIKES = getattr(settings, 'FACEBOOK_STORE_LIKES', False)
FACEBOOK_STORE_FRIENDS = getattr(settings, 'FACEBOOK_STORE_FRIENDS', False)
# if we should be using celery to do the above two,
# recommended if you want to store friends or likes
FACEBOOK_CELERY_STORE = getattr(settings, 'FACEBOOK_CELERY_STORE', False)
# use celery for updating tokens, recommended since it's quite slow
FACEBOOK_CELERY_TOKEN_EXTEND = getattr(
    settings, 'FACEBOOK_CELERY_TOKEN_EXTEND', False)

FACEBOOK_DEBUG_REDIRECTS = getattr(settings, 'FACEBOOK_DEBUG_REDIRECTS', False)

#READ only mode, convenient when doing load testing etc.
FACEBOOK_READ_ONLY = getattr(settings, 'FACEBOOK_READ_ONLY', False)

# check for required settings
required_settings = ['FACEBOOK_APP_ID', 'FACEBOOK_APP_SECRET']
locals_dict = locals()
for setting_name in required_settings:
    setting_available = locals_dict.get(setting_name) is not None
    assert setting_available, 'Please provide setting %s' % setting_name

# Allow custom registration template
FACEBOOK_REGISTRATION_TEMPLATE = getattr(settings,
                                         'FACEBOOK_REGISTRATION_TEMPLATE', ['django_facebook/registration.html', 'registration/registration_form.html'])

# Allow custom signup form
FACEBOOK_REGISTRATION_FORM = getattr(settings,
                                     'FACEBOOK_REGISTRATION_FORM', None)

default_registration_backend = 'django_facebook.registration_backends.FacebookRegistrationBackend'
FACEBOOK_REGISTRATION_BACKEND = getattr(
    settings, 'FACEBOOK_REGISTRATION_BACKEND', default_registration_backend)

#Fall back redirect location when no other location was found
FACEBOOK_LOGIN_DEFAULT_REDIRECT = getattr(
    settings, 'FACEBOOK_LOGIN_DEFAULT_REDIRECT', '/')

# Force profile update every login
FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN = getattr(
    settings, 'FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN', False)


#Retry an open graph share 6 times (once every 15 minutes)
FACEBOOK_OG_SHARE_RETRIES = getattr(settings, 'FACEBOOK_OG_SHARE_RETRIES', 6)
#Retry a failed open graph share (when we have an updated token) for this number of days
FACEBOOK_OG_SHARE_RETRY_DAYS = getattr(
    settings, 'FACEBOOK_OG_SHARE_RETRY_DAYS', 7)
FACEBOOK_OG_SHARE_DB_TABLE = getattr(
    settings, 'FACEBOOK_OG_SHARE_DB_TABLE', None)


# Force profile update every login
FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN = getattr(
    settings, 'FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN', False)

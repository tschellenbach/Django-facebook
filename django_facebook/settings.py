from django.conf import settings


# these 3 should be provided by your app
FACEBOOK_APP_ID = getattr(settings, 'FACEBOOK_APP_ID', None)
FACEBOOK_APP_SECRET = getattr(settings, 'FACEBOOK_APP_SECRET', None)
FACEBOOK_DEFAULT_SCOPE = getattr(settings, 'FACEBOOK_DEFAULT_SCOPE', [
    'email', 'user_about_me', 'user_birthday'])

# Absolute canvas page url as per facebook standard
FACEBOOK_CANVAS_PAGE = getattr(settings, 'FACEBOOK_CANVAS_PAGE',
                               'http://apps.facebook.com/fashiolista_test/')

# These you don't need to change
FACEBOOK_HIDE_CONNECT_TEST = getattr(settings,
                                     'FACEBOOK_HIDE_CONNECT_TEST', True)
# Track all raw data coming in from FB
FACEBOOK_TRACK_RAW_DATA = getattr(settings, 'FACEBOOK_TRACK_RAW_DATA', False)

# if we should store friends and likes
FACEBOOK_STORE_LIKES = getattr(settings, 'FACEBOOK_STORE_LIKES', False)
FACEBOOK_STORE_FRIENDS = getattr(settings, 'FACEBOOK_STORE_FRIENDS', False)
# if we should be using celery to do the above two,
# recommended if you want to store friends or likes
FACEBOOK_CELERY_STORE = getattr(settings, 'FACEBOOK_CELERY_STORE', False)

FACEBOOK_DEBUG_REDIRECTS = getattr(settings, 'FACEBOOK_DEBUG_REDIRECTS', False)
FACEBOOK_STORE_ALL_ACCESS_TOKENS = getattr(settings, 'FACEBOOK_STORE_ALL_ACCESS_TOKENS', False) 

# check for required settings
required_settings = ['FACEBOOK_APP_ID', 'FACEBOOK_APP_SECRET']
locals_dict = locals()
for setting_name in required_settings:
    setting_available = locals_dict.get(setting_name) is not None
    assert setting_available, 'Please provide setting %s' % setting_name

# Allow custom registration template
FACEBOOK_REGISTRATION_TEMPLATE = getattr(settings,
    'FACEBOOK_REGISTRATION_TEMPLATE', 'registration/registration_form.html')

# Allow custom signup form
FACEBOOK_REGISTRATION_FORM = getattr(settings,
    'FACEBOOK_REGISTRATION_FORM', None)

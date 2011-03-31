from django.conf import settings



FACEBOOK_API_KEY = getattr(settings, 'FACEBOOK_API_KEY', None)
FACEBOOK_APP_ID = getattr(settings, 'FACEBOOK_APP_ID', None)
FACEBOOK_APP_SECRET = getattr(settings, 'FACEBOOK_APP_SECRET', None)

#Absolute canvas page url as per facebook standard
FACEBOOK_CANVAS_PAGE = getattr(settings, 'FACEBOOK_CANVAS_PAGE', 'http://apps.facebook.com/fashiolista_test/')



#These you don't need to change
FACEBOOK_HIDE_CONNECT_TEST = getattr(settings, 'FACEBOOK_HIDE_CONNECT_TEST', True)

#check for required settings
required_settings = ['FACEBOOK_API_KEY', 'FACEBOOK_APP_ID', 'FACEBOOK_APP_SECRET']
locals_dict = locals()
for setting_name in required_settings:
    assert locals_dict.get(setting_name) is not None, 'Please provide setting %s' % setting_name

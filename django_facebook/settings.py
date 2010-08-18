from django.conf import settings
'''
Step 1 Defined the following settings in your settings file
Step 2 add the following line to your authentication backends
'django_facebook.auth_backends.FacebookBackend',
'''
FACEBOOK_FAKE_PASSWORD = getattr(settings, 'FACEBOOK_FAKE_PASSWORD', True)
FACEBOOK_JINJA = getattr(settings, 'FACEBOOK_JINJA', True)
FACEBOOK_APP_ID = getattr(settings, 'FACEBOOK_APP_ID', False)
FACEBOOK_APP_SECRET = getattr(settings, 'FACEBOOK_APP_SECRET', False)


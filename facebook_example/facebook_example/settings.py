# Django settings for facebook_example project.
import os
import django
django_version = django.VERSION
# some complications related to our travis testing setup
DJANGO = os.environ.get('DJANGO', '1.5.1')
MODE = os.environ.get('MODE', 'standalone')
CUSTOM_USER_MODEL = bool(int(os.environ.get('CUSTOM_USER_MODEL', '1')))

if DJANGO != '1.5.1':
    CUSTOM_USER_MODEL = False

FACEBOOK_APP_ID = '215464901804004'
FACEBOOK_APP_SECRET = '0aceba27823a9dfefa955f76949fa4b4'
TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'django_facebook.context_processors.facebook',
]

if django_version >= (1, 4, 0):
    TEMPLATE_CONTEXT_PROCESSORS.append('django.core.context_processors.tz')
    
AUTHENTICATION_BACKENDS = (
    'django_facebook.auth_backends.FacebookBackend',
    'django.contrib.auth.backends.ModelBackend',
)

if CUSTOM_USER_MODEL:
    AUTH_USER_MODEL = 'django_facebook.FacebookCustomUser'
else:
    AUTH_USER_MODEL = 'auth.User'
    AUTH_PROFILE_MODULE = 'member.UserProfile'

BASE_ROOT = os.path.abspath(
    os.path.join(os.path.split(__file__)[0]))
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_ROOT, 'media/')
STATICFILES_ROOT = os.path.join(BASE_ROOT, 'static/')


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'facebook_example_db',  # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',  # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True


# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '1r#u)ta4&+!1al0+defnyol*jg6=n+dlz*#be!2-kf_x@&1-wh'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'facebook_example.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'facebook_example.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'django_facebook',
    'member',
    'south',
    'open_facebook',
)



# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
FILTERS = {
    'require_debug_false': {
        '()': 'django.utils.log.RequireDebugFalse'
    }
}

MAIL_ADMINS = {
    'level': 'ERROR',
    'class': 'django.utils.log.AdminEmailHandler'
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'open_facebook': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django_facebook': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
LOGGING['handlers']['mail_admins'] = MAIL_ADMINS

if django_version > (1, 4, 0):
    LOGGING['filters'] = FILTERS
    MAIL_ADMINS['filters'] = ['require_debug_false']
    LOGGING['handlers']['mail_admins'] = MAIL_ADMINS

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

if MODE == 'django_registration':
    FACEBOOK_REGISTRATION_BACKEND = 'facebook_example.registration_backends.DjangoRegistrationDefaultBackend'
    INSTALLED_APPS += (
        'registration',
    )
    ACCOUNT_ACTIVATION_DAYS = 10
elif MODE == 'userena':
    '''
    Settings based on these docs
    http://docs.django-userena.org/en/latest/installation.html#installing-django-userena
    '''
    FACEBOOK_REGISTRATION_BACKEND = 'django_facebook.registration_backends.UserenaBackend'
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

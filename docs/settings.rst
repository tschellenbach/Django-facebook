Settings
========

.. toctree::
   :maxdepth: 2

.. automodule:: django_facebook.settings
    :members:

Security settings
*****************

**FACEBOOK_APP_ID**

Your facebook app id

**FACEBOOK_APP_SECRET**

Your facebook app secret

**FACEBOOK_DEFAULT_SCOPE**

The default scope we should use, note that registration will break without email
Defaults to
['email', 'user_birthday']

Customizing registration
************************

**FACEBOOK_REGISTRATION_BACKEND**

Allows you to overwrite the registration backend class
Specify a full path to a class 
(defaults to django_facebook.registration_backends.FacebookRegistrationBackend)

Likes and Friends
*****************

**FACEBOOK_STORE_LIKES**

If we should store likes

**FACEBOOK_STORE_FRIENDS**

If we should store friends

**FACEBOOK_CELERY_STORE**

If celery should be used to retrieve friends and likes

**FACEBOOK_CELERY_TOKEN_EXTEND**

Use celery for updating tokens, recommended since it's quite slow





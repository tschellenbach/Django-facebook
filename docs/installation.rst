Installation
------------

**0.) Create a Facebook App**

You need a facebook app to use the open graph API and make the login process work.
If you don't have a facebook app, now is the time to create one.
You can create a facebook app at `this url <http://www.facebook.com/developers/createapp.php>`_.

Facebook authentication only works if the domain you are working on matches your app domain.
Be sure to configure the right app domain in your facebook application settings.

An example:

Your site is www.fashiolista.com, your app domain is set to fashiolista.com and you do your development at ``local.fashiolista.com``.
If you try to authenticate with Facebook from a different domain you will get an authentication error.

**1.) Pip install**

.. code-block:: bash

    pip install django_facebook

**2.) Settings**

Define the following settings in your settings.py file:

::

    FACEBOOK_APP_ID
    FACEBOOK_APP_SECRET

**Context processor**

add django facebook to your installed apps::

    'django_facebook',

Add this line to your context processors (``TEMPLATE_CONTEXT_PROCESSORS`` setting)::

    'django_facebook.context_processors.facebook',
    # and add request if you didn't do so already
    'django.core.context_processors.request',

The full setting on a new django 1.5 app looks like this

.. code-block:: python

  TEMPLATE_CONTEXT_PROCESSORS = (
      'django.contrib.auth.context_processors.auth',
      'django.core.context_processors.debug',
      'django.core.context_processors.i18n',
      'django.core.context_processors.media',
      'django.core.context_processors.static',
      'django.core.context_processors.tz',
      'django.core.context_processors.request',
      'django.contrib.messages.context_processors.messages',
      'django_facebook.context_processors.facebook',
  )

**Auth backend**

Add this to your ``AUTHENTICATION_BACKENDS`` setting::

    'django_facebook.auth_backends.FacebookBackend',

The full setting on a new django 1.5 app looks like this::

  AUTHENTICATION_BACKENDS = (
      'django_facebook.auth_backends.FacebookBackend',
      'django.contrib.auth.backends.ModelBackend',
  )


**3.) Urls**
Now, add this line to your url config::

    (r'^facebook/', include('django_facebook.urls')),
    (r'^accounts/', include('django_facebook.auth_urls')), #Don't add this line if you use django registration or userena for registration and auth.


**4.) Update your models**

The following step depends on your version of Django. Django versions before 1.5 need to use a custom profile model.
Whereas Django 1.5 and up can use a custom user model.

**A. Custom user model**

If you don't already have a custom user model, simply uses the provided model by setting your AUTH_USER_MODEL to FacebookCustomUser::

    AUTH_USER_MODEL = 'django_facebook.FacebookCustomUser'

Alternatively use the abstract model provided in django_facebook.models.FacebookProfileModel

.. note::
    Please note that Django Facebook does not support custom user models with ``USERNAME_FIELD`` different than ``username``.

**B. Profile model**

If you don't already have a custom Profile model, simply uses the provided model by setting your AUTH_PROFILE_MODULE to FacebookProfile::

    AUTH_PROFILE_MODULE = 'django_facebook.FacebookProfile'

Be sure to run manage.py syncdb after setting this up.

Otherwise Django Facebook provides an abstract model which you can inherit like this.
::
    from django.db import models
    from django.dispatch.dispatcher import receiver
    from django_facebook.models import FacebookModel
    from django.db.models.signals import post_save
    from django_facebook.utils import get_user_model, get_profile_model
    from your_project import settings


    class MyCustomProfile(FacebookModel):
        user = models.OneToOneField(settings.AUTH_USER_MODEL)

        @receiver(post_save)
        def create_profile(sender, instance, created, **kwargs):
            """Create a matching profile whenever a user object is created."""
            if sender == get_user_model():
                user = instance
                profile_model = get_profile_model()
            if profile_model == MyCustomProfile and created:
                profile, new = MyCustomProfile.objects.get_or_create(user=instance)``

Remember to update AUTH_PROFILE_MODULE in settings to your new profile.
Don't forget to update your database using syncdb or south after this step.

Note: You need a profile model attached to every user model. For new accounts this will get created automatically, but you will need to migrate older accounts.

**Congratulations**

Right now you should have a working registration/connect/login in flow available at /facebook/example/! (settings.DEBUG needs to be set to True)
Test if everything is working and ensure you didn't miss a step somewhere.
If you encounter any difficulties please open an issue.

Of course you now want to customize things like the login button, the page after registration etc.
This is explained in the integration section.

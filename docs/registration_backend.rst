Redirects
---------

For most applications you can simply use the next, register next and error next parameters to control the post registration flow.
The "next" parameter provides the default next page for login, connect, error or register actions. "register_next" and "error_next" allow you to customize the next page for those specific scenarios. This is usefull when you for instance want to show an introduction page to new users.

Flows

   * Login (login_next, next, default)
   * Connect (connect_next, next, default)
   * Register (register_next, next, default)
   * Error (error_next, next, default)

The default redirect is specified by the FACEBOOK_LOGIN_DEFAULT_REDIRECT setting.

If the default customizability isn't adequate for your needs you can also subclass the registration backend.

::

    class CustomBackend(FacebookRegistrationBackend):
        def post_connect(action):
            # go as crazy as you want, just be sure to return a response
            response = HttpRedirect('/something/')
            if action is CONNECT_ACTIONS.LOGIN:
                response = HttpRedirect('/')
            return response


Registration Backends
---------------------

**Registration Backends**

By default Django Facebook ships with its own registration system.
It provides a basic manual registration flow and the option to connect with Facebook.

If you are looking for something more complicated it's possible to integrate with Userena or Django Registration.
To add support for these systems we use the FACEBOOK_REGISTRATION_BACKEND setting.


**Django Registration support**
Create a registration backend which subclasses both Django Facebook and Django Registration's
registration backend. An example is included in facebook_example/registration_backends.py

::
    
    # in registration_backends.py
    class DjangoRegistrationDefaultBackend(DefaultBackend, NooptRegistrationBackend):
        '''
        The redirect behaviour will still be controlled by the
            post_error
            post_connect
        functions
        the form and other settings will be taken from the default backend
        '''
        pass

    # in your settings file
    FACEBOOK_REGISTRATION_BACKEND = 'registration.backends.default.DefaultBackend'

**Django Userena support**

Django Userena is easier to work with than Django Registration.
It is however hard to setup unittesting with Userena, so the integration between Django Facebook and Userena might not work.
Please report any bugs you run into.

::

    FACEBOOK_REGISTRATION_BACKEND = 'django_facebook.registration_backends.UserenaBackend'


Also have a look at the userena settings file in the facebook example project.
It provides a clear example of how to configure Userena and Django Facebook to work together.

**Other registration systems**

Supporting any other registration system is quite easy.
Adjust the above settings to point to your own code.
Note that the form's save method needs to return the new user object.

Also have a look at the API docs for :class:`.FacebookRegistrationBackend`
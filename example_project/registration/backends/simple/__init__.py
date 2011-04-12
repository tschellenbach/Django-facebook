from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth.models import User

from registration import signals
from registration.forms import RegistrationForm


class SimpleBackend(object):
    """
    A registration backend which implements the simplest possible
    workflow: a user supplies a username, email address and password
    (the bare minimum for a useful account), and is immediately signed
    up and logged in.
    
    """
    def register(self, request, **kwargs):
        """
        Create and immediately log in a new user.
        
        """
        username, email, password = kwargs['username'], kwargs['email'], kwargs['password1']
        User.objects.create_user(username, email, password)
        
        # authenticate() always has to be called before login(), and
        # will return the user we just created.
        new_user = authenticate(username=username, password=password)
        login(request, new_user)
        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)
        return new_user

    def activate(self, **kwargs):
        raise NotImplementedError

    def registration_allowed(self, request):
        """
        Indicate whether account registration is currently permitted,
        based on the value of the setting ``REGISTRATION_OPEN``. This
        is determined as follows:

        * If ``REGISTRATION_OPEN`` is not specified in settings, or is
          set to ``True``, registration is permitted.

        * If ``REGISTRATION_OPEN`` is both specified and set to
          ``False``, registration is not permitted.
        
        """
        return getattr(settings, 'REGISTRATION_OPEN', True)

    def get_form_class(self, request):
        return RegistrationForm

    def post_registration_redirect(self, request, user):
        """
        After registration, redirect to the user's account page.
        
        """
        return (user.get_absolute_url(), (), {})

    def post_activation_redirect(self, request, user):
        raise NotImplementedError

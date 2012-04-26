from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth.models import User

from django_facebook import signals
from django_facebook.forms import FacebookRegistrationFormUniqueEmail


class FacebookRegistrationBackend(object):
    """
    A backend compatible with Django Registration
    It is extremly simple and doesn't handle things like redirects etc
    (These are already handled by Django Facebook)
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
        return getattr(settings, 'REGISTRATION_OPEN', True)

    def get_form_class(self, request):
        return FacebookRegistrationFormUniqueEmail

    def post_registration_redirect(self, request, user):
        '''
        Handled by the Django Facebook app
        '''
        raise NotImplementedError

    def post_activation_redirect(self, request, user):
        '''
        Handled by the Django Facebook app
        '''
        raise NotImplementedError

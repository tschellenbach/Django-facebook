from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth.models import User

from django_facebook import signals
from django_facebook.forms import FacebookRegistrationFormUniqueEmail
from django_facebook import settings as facebook_settings


class NooptRegistrationBackend(object):
    '''
    Noopt backends forms the basis of support for backends
    which handle the actual registration in the registration form
    '''
    def get_form_class(self, request):
        return FacebookRegistrationFormUniqueEmail

    def get_registration_template(self):
        template = facebook_settings.FACEBOOK_REGISTRATION_TEMPLATE
        return template

    def register(self, request, **kwargs):
        pass

    def activate(self, **kwargs):
        raise NotImplementedError

    def registration_allowed(self, request):
        return getattr(settings, 'REGISTRATION_OPEN', True)

    def post_registration_redirect(self, request, user):
        '''
        Handled by the Django Facebook app
        '''
        response = user.get_profile().post_facebook_registration(request)
        return response

    def post_activation_redirect(self, request, user):
        raise NotImplementedError


class FacebookRegistrationBackend(NooptRegistrationBackend):
    """
    A backend compatible with Django Registration
    It is extremly simple and doesn't handle things like redirects etc
    (These are already handled by Django Facebook)
    """
    def register(self, request, **kwargs):
        """
        Create and immediately log in a new user.

        """
        username, email, password = kwargs['username'], kwargs[
            'email'], kwargs['password1']
        #Create user doesn't accept additional parameters,
        new_user = User.objects.create_user(username, email, password)

        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)
        authenticated_user = self.authenticate(request, username, password)
        return authenticated_user

    def authenticate(self, request, username, password):
        # authenticate() always has to be called before login(), and
        # will return the user we just created.
        new_user = authenticate(username=username, password=password)
        login(request, new_user)
        return new_user


class UserenaBackend(NooptRegistrationBackend):
    def get_form_class(self, request):
        from userena.forms import SignupForm
        return SignupForm

    def get_registration_template(self):
        template = 'userena/signup_form.html'
        return template


class OldDjangoRegistrationBackend(NooptRegistrationBackend):
    def get_form_class(self, request):
        from registration.forms import RegistrationFormUniqueEmail
        return RegistrationFormUniqueEmail

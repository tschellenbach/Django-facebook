from django.conf import settings
from django.contrib.auth import authenticate, login
from django_facebook import settings as facebook_settings, signals
from django_facebook.connect import CONNECT_ACTIONS
from django_facebook.forms import FacebookRegistrationFormUniqueEmail
from django_facebook.utils import get_user_model, next_redirect, \
    error_next_redirect
from functools import partial
from django.contrib.auth import get_backends


class NooptRegistrationBackend(object):

    '''
    Noopt backends forms the basis of support for backends
    which handle the actual registration in the registration form
    '''

    def get_form_class(self, request):
        '''
        Returns the form class to use for registration

        :param request: the request object
        '''
        return FacebookRegistrationFormUniqueEmail

    def get_registration_template(self):
        '''
        Returns the template to use for registration
        '''
        template = facebook_settings.FACEBOOK_REGISTRATION_TEMPLATE
        return template

    def register(self, request, form=None, **kwargs):
        '''
        Implement your registration logic in this method

        :param request: the request object
        :param form: the form with the users data
        :param kwargs: additional data
        '''
        pass

    def activate(self, **kwargs):
        raise NotImplementedError

    def registration_allowed(self, request):
        return getattr(settings, 'REGISTRATION_OPEN', True)

    def post_error(self, request, additional_params=None):
        '''
        Handles the redirect after connecting
        '''
        response = error_next_redirect(
            request,
            additional_params=additional_params)
        return response

    def post_connect(self, request, user, action):
        '''
        Handles the redirect after connecting
        '''
        default_url = facebook_settings.FACEBOOK_LOGIN_DEFAULT_REDIRECT
        base_next_redirect = partial(
            next_redirect, request, default=default_url)

        if action is CONNECT_ACTIONS.LOGIN:
            response = base_next_redirect(next_key=['login_next', 'next'])
        elif action is CONNECT_ACTIONS.CONNECT:
            response = base_next_redirect(next_key=['connect_next', 'next'])
        elif action is CONNECT_ACTIONS.REGISTER:
            response = base_next_redirect(next_key=['register_next', 'next'])

        return response

    def post_activation_redirect(self, request, user):
        raise NotImplementedError


class FacebookRegistrationBackend(NooptRegistrationBackend):

    """
    A backend compatible with Django Registration
    It is extremly simple and doesn't handle things like redirects etc
    (These are already handled by Django Facebook)
    """

    def register(self, request, form=None, **kwargs):
        """
        Create and immediately log in a new user.

        """
        username, email, password = kwargs['username'], kwargs[
            'email'], kwargs['password1']
        # Create user doesn't accept additional parameters,
        new_user = get_user_model(
        ).objects.create_user(username, email, password)

        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)
        authenticated_user = self.authenticate(request, username, password)
        return authenticated_user

    def authenticate(self, request, username, password):
        # authenticate() always has to be called before login(), and
        # will return the user we just created.
        authentication_details = dict(username=username, password=password)
        user = authenticate(**authentication_details)
        login(request, user)

        if user is None or not user.is_authenticated():
            backends = get_backends()
            msg_format = 'Authentication using backends %s and data %s failed'
            raise ValueError(msg_format % (backends, authentication_details))

        return user


class UserenaBackend(NooptRegistrationBackend):

    def register(self, request, form, **kwargs):
        new_user = form.save()
        return new_user

    def get_form_class(self, request):
        from userena.forms import SignupForm
        return SignupForm

    def get_registration_template(self):
        if facebook_settings.FACEBOOK_REGISTRATION_TEMPLATE == facebook_settings.default_registration_template:
            template = 'userena/signup_form.html'
        return template


class OldDjangoRegistrationBackend(NooptRegistrationBackend):

    def get_form_class(self, request):
        from registration.forms import RegistrationFormUniqueEmail
        return RegistrationFormUniqueEmail

from __future__ import with_statement
from django.contrib.auth.models import AnonymousUser, User
from django_facebook import settings as facebook_settings
from django_facebook import exceptions as facebook_exceptions
from django_facebook.auth_backends import FacebookBackend
from django_facebook.connect import (_register_user, connect_user,
                                     CONNECT_ACTIONS)
from django_facebook.tests_utils.base import FacebookTest
from django_facebook.utils import get_profile_class
from django_facebook.api import (get_facebook_graph, FacebookUserConverter,
                                 get_persistent_graph)
from django_facebook import signals
import logging
from open_facebook.api import FacebookConnection
from functools import partial
from django_facebook.utils import cleanup_oauth_url

logger = logging.getLogger(__name__)


__doctests__ = ['django_facebook.api']


'''
TODO
The views are currently untested,
only the underlying functionality is.
(need to fake facebook cookie stuff to correctly test the views)
'''


class UserConnectTest(FacebookTest):
    '''
    Tests the connect user functionality
    '''
    fixtures = ['users.json']

    def test_persistent_graph(self):
        from django.test import RequestFactory
        request = RequestFactory()
        request.session = {}
        request.user = AnonymousUser()
        get_persistent_graph(request, access_token='short_username')
        
    def test_gender_matching(self):
        from django.test import RequestFactory
        request = RequestFactory()
        request.session = {}
        request.user = AnonymousUser()
        graph = get_persistent_graph(request, access_token='paul')
        converter = FacebookUserConverter(graph)
        base_data = converter.facebook_profile_data()
        self.assertEqual(base_data['gender'], 'male')
        data = converter.facebook_registration_data()
        self.assertEqual(data['gender'], 'm')
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(user.get_profile().gender, 'm')

    def test_full_connect(self):
        #going for a register, connect and login
        graph = get_facebook_graph(access_token='short_username')
        FacebookUserConverter(graph)
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(action, CONNECT_ACTIONS.REGISTER)
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(action, CONNECT_ACTIONS.CONNECT)
        self.request.user = AnonymousUser()
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(action, CONNECT_ACTIONS.LOGIN)

    def test_utf8(self):
        graph = get_facebook_graph(access_token='unicode_string')
        facebook = FacebookUserConverter(graph)
        facebook.facebook_profile_data()
        action, user = connect_user(self.request, facebook_graph=graph)

    def test_invalid_token(self):
        self.assertRaises(AssertionError,
                          connect_user, self.request, access_token='invalid')

    def test_no_email_registration(self):
        self.assertRaises(facebook_exceptions.IncompleteProfileError,
                          connect_user, self.request, access_token='no_email')

    def test_current_user(self):
        facebook = get_facebook_graph(access_token='tschellenbach')
        action, user = connect_user(self.request, facebook_graph=facebook)
        self.assertEqual(action, CONNECT_ACTIONS.LOGIN)

    def test_new_user(self):
        facebook = get_facebook_graph(access_token='new_user')
        action, user = connect_user(self.request, facebook_graph=facebook)

    def test_short_username(self):
        facebook = get_facebook_graph(access_token='short_username')
        action, user = connect_user(self.request, facebook_graph=facebook)
        self.assertTrue(len(user.username) > 4)
        self.assertEqual(action, CONNECT_ACTIONS.REGISTER)

    def test_gender(self):
        graph = get_facebook_graph(access_token='new_user')
        facebook = FacebookUserConverter(graph)
        data = facebook.facebook_registration_data()
        self.assertEqual(data['gender'], 'm')

    def test_double_username(self):
        '''
        This used to give an error with duplicate usernames
        with different capitalization
        '''
        facebook = get_facebook_graph(access_token='short_username')
        action, user = connect_user(self.request, facebook_graph=facebook)
        user.username = 'Thierry_schellenbach'
        user.save()
        self.request.user = AnonymousUser()
        facebook = get_facebook_graph(access_token='same_username')
        action, new_user = connect_user(self.request, facebook_graph=facebook)
        self.assertNotEqual(user.username, new_user.username)
        self.assertNotEqual(user.id, new_user.id)

    def test_registration_form(self):
        '''
        Django_facebook should use user supplied registration form if given
        '''
        facebook_settings.FACEBOOK_REGISTRATION_FORM = 'django_facebook.tests_utils.forms.SignupForm'
        facebook = get_facebook_graph(access_token='short_username')
        action, user = connect_user(self.request, facebook_graph=facebook)
        # The test form always sets username to test form
        self.assertEqual(user.username, 'Test form')


class AuthBackend(FacebookTest):
    def test_auth_backend(self):
        backend = FacebookBackend()
        facebook = get_facebook_graph(access_token='new_user')
        action, user = connect_user(self.request, facebook_graph=facebook)
        facebook_email = user.email
        facebook_id = user.get_profile().facebook_id
        auth_user = backend.authenticate(facebook_email=facebook_email)
        self.assertEqual(auth_user, user)

        auth_user = backend.authenticate(facebook_id=facebook_id)
        self.assertEqual(auth_user, user)

        auth_user = backend.authenticate(facebook_id=facebook_id,
                                         facebook_email=facebook_email)
        self.assertEqual(auth_user, user)

        auth_user = backend.authenticate()
        self.assertIsNone(auth_user)


class ErrorMappingTest(FacebookTest):
    def test_mapping(self):
        from open_facebook import exceptions as facebook_exceptions
        raise_something = partial(FacebookConnection.raise_error, 0,
                                  "(#200) The user hasn't authorized the " \
                                  "application to perform this action")
        self.assertRaises(facebook_exceptions.PermissionException,
                          raise_something)


class OAuthUrlTest(FacebookTest):
    def _test_equal(self, url, output):
        converted = cleanup_oauth_url(url)
        self.assertEqual(converted, output)

    def test_url(self):
        url = 'http://www.google.com/'
        output = 'http://www.google.com/'
        self._test_equal(url, output)

        url = 'http://www.google.com/?code=a'
        output = 'http://www.google.com/'
        self._test_equal(url, output)

        url = 'http://www.google.com/?code=a&b=c&d=c'
        output = 'http://www.google.com/?b=c&d=c'
        self._test_equal(url, output)


class SignalTest(FacebookTest):
    '''
    Tests that signals fire properly
    '''

    def test_user_registered_signal(self):
        # Ensure user registered, pre update and post update signals fire

        def user_registered(sender, user, facebook_data, **kwargs):
            user.registered_signal = True

        def pre_update(sender, profile, facebook_data, **kwargs):
            profile.pre_update_signal = True

        def post_update(sender, profile, facebook_data, **kwargs):
            profile.post_update_signal = True

        Profile = get_profile_class()
        signals.facebook_user_registered.connect(user_registered, sender=User)
        signals.facebook_pre_update.connect(pre_update, sender=Profile)
        signals.facebook_post_update.connect(post_update, sender=Profile)

        graph = get_facebook_graph(access_token='short_username')
        facebook = FacebookUserConverter(graph)
        user = _register_user(self.request, facebook)
        self.assertEqual(hasattr(user, 'registered_signal'), True)
        self.assertEqual(hasattr(user.get_profile(),
                                 'pre_update_signal'), True)
        self.assertEqual(hasattr(user.get_profile(),
                                 'post_update_signal'), True)

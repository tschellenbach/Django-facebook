from __future__ import with_statement
from django.contrib.auth.models import AnonymousUser
from django.core.urlresolvers import reverse
from django.test.client import Client, RequestFactory
from django_facebook import exceptions as facebook_exceptions, \
    settings as facebook_settings, signals
from django_facebook.utils import get_user_model
from django_facebook.api import get_facebook_graph, FacebookUserConverter, \
    get_persistent_graph
from django_facebook.auth_backends import FacebookBackend
from django_facebook.connect import _register_user, connect_user, \
    CONNECT_ACTIONS
from django_facebook.tests_utils.base import FacebookTest, LiveFacebookTest, \
    RequestMock
from django_facebook.utils import cleanup_oauth_url, get_profile_class,\
    CanvasRedirect
from functools import partial
from mock import Mock, patch
from open_facebook.api import FacebookConnection, FacebookAuthorization,\
    OpenFacebook
from open_facebook.exceptions import FacebookSSLError, FacebookURLError
import logging
import mock
from django_facebook.middleware import FacebookCanvasMiddleWare
from django.contrib.sessions.middleware import SessionMiddleware


logger = logging.getLogger(__name__)
__doctests__ = ['django_facebook.api']


class TestUserTest(LiveFacebookTest):
    def test_create_test_user(self):
        #Also, somehow unittest.skip doesnt work with travis ci?
        return 'Skipping since you might have created test users manually, lets not delete them :)'
        #start by clearing out our test users (maybe this isnt safe to use in testing)
        #if other people create test users manualy this could be annoying
        app_access_token = FacebookAuthorization.get_cached_app_access_token()
        FacebookAuthorization.delete_test_users(app_access_token)
        #the permissions for which we want a test user
        permissions = ['email', 'publish_actions']
        #gets the test user object
        test_user = FacebookAuthorization.get_or_create_test_user(
            app_access_token, permissions)
        graph = test_user.graph()
        me = graph.me()
        assert me


class ExtendTokenTest(LiveFacebookTest):
    def test_extend_token(self):
        return 'this doesnt work in travis, but locally its fine... weird'
        app_access_token = FacebookAuthorization.get_cached_app_access_token()
        test_user = FacebookAuthorization.get_or_create_test_user(
            app_access_token)
        access_token = test_user.access_token
        results = FacebookAuthorization.extend_access_token(access_token)
        if 'access_token' not in results:
            raise ValueError('we didnt get a fresh token')


class UserConnectViewTest(FacebookTest):
    fixtures = ['users.json']

    def test_connect(self):
        '''
        Test if we can do logins
        django_facebook.connect.connect_user
        '''
        user = get_user_model().objects.all()[:1][0]
        url = reverse('facebook_connect')

        #see if the basics don't give errors
        response = self.client.get('%s?facebook_login=a' % url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('%s?facebook_login=0' % url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('%s?facebook_login=' % url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        #test registration flow
        from django_facebook.connect import connect_user
        with patch('django_facebook.views.connect_user', return_value=(CONNECT_ACTIONS.REGISTER, user)) as wrapped_connect:
            post_data = dict(access_token='short_username',
                             next='%s?register=1' % url, facebook_login=1)
            response = self.client.post(url, post_data, follow=True)
            self.assertEqual(wrapped_connect.call_count, 1)
            self.assertIn('register', response.redirect_chain[0][0])
            self.assertEqual(response.status_code, 200)

        #user register next instead of next
        with patch('django_facebook.views.connect_user', return_value=(CONNECT_ACTIONS.REGISTER, user)) as wrapped_connect:
            post_data = dict(access_token='short_username', register_next='%s?register=1' % url, facebook_login=1)
            response = self.client.post(url, post_data, follow=True)
            self.assertEqual(wrapped_connect.call_count, 1)
            self.assertIn('register', response.redirect_chain[0][0])
            self.assertEqual(response.status_code, 200)

        #test login
        with patch('django_facebook.views.connect_user', return_value=(CONNECT_ACTIONS.LOGIN, user)) as wrapped_connect:
            post_data = dict(access_token='short_username',
                             next='%s?loggggg=1' % url, facebook_login=1)
            response = self.client.post(url, post_data, follow=True)
            self.assertEqual(wrapped_connect.call_count, 1)
            self.assertIn('?loggggg=1', response.redirect_chain[0][0])
            self.assertEqual(response.status_code, 200)

        #test connect
        with patch('django_facebook.views.connect_user', return_value=(CONNECT_ACTIONS.CONNECT, user)) as wrapped_connect:
            post_data = dict(access_token='short_username',
                             next='%s?loggggg=1' % url, facebook_login=1)
            response = self.client.post(url, post_data, follow=True)
            self.assertEqual(wrapped_connect.call_count, 1)
            assert '?loggggg=1' in response.redirect_chain[0][0]
            self.assertEqual(response.status_code, 200)

        #test connect
        from django_facebook import exceptions as facebook_exceptions
        profile_error = facebook_exceptions.IncompleteProfileError()
        profile_error.form = None
        with patch('django_facebook.views.connect_user', return_value=(CONNECT_ACTIONS.REGISTER, user), side_effect=profile_error) as wrapped_connect:
            post_data = dict(access_token='short_username',
                             next='%s?loggggg=1' % url, facebook_login=1)
            response = self.client.post(url, post_data, follow=True)
            self.assertEqual(wrapped_connect.call_count, 1)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context)
            assert response.template.name in facebook_settings.FACEBOOK_REGISTRATION_TEMPLATE or response.template.name == facebook_settings.FACEBOOK_REGISTRATION_TEMPLATE

    def test_slow_connect(self):
        '''
        Test if we can do logins
        django_facebook.connect.connect_user
        '''
        url = reverse('facebook_connect')

        #test super slow Facebook
        errors = [FacebookSSLError(), FacebookURLError(
            '<urlopen error _ssl.c:489: The handshake operation timed out>')]
        for error in errors:
            with patch('django_facebook.views.FacebookUserConverter') as converter:
                instance = converter.return_value
                instance.is_authenticated = Mock(side_effect=error)
                post_data = dict(access_token='short_username',
                                 next='%s?loggggg=1' % url, facebook_login=1)
                response = self.client.post(url, post_data, follow=True)
                self.assertEqual(instance.is_authenticated.call_count, 1)
                self.assertTrue(response.context)
                assert '?loggggg=1' in response.redirect_chain[0][0]


class OpenGraphShareTest(FacebookTest):
    fixtures = ['users.json']

    def test_follow_og_share(self):
        from django_facebook.models import OpenGraphShare
        user_url = 'http://www.fashiolista.com/style/neni/'
        kwargs = dict(item=user_url)
        user = get_user_model().objects.all()[:1][0]
        from django.contrib.contenttypes.models import ContentType
        love_content_type = ContentType.objects.get(
            app_label='auth', model='user')
        share = OpenGraphShare.objects.create(
            user_id=user.id,
            facebook_user_id=13123123,
            action_domain='fashiolista:follow',
            content_type=love_content_type,
            object_id=user.id,
        )
        share.set_share_dict(kwargs)
        share.save()
        share.send()

    def test_follow_og_share_error(self):
        from django_facebook.models import OpenGraphShare
        user_url = 'http://www.fashiolista.com/style/neni/'
        kwargs = dict(item=user_url)
        user = get_user_model().objects.all()[:1][0]
        profile = user.get_profile()
        profile.facebook_open_graph = True
        profile.save()

        from django.contrib.contenttypes.models import ContentType
        love_content_type = ContentType.objects.get(
            app_label='auth', model='user')
        share = OpenGraphShare.objects.create(
            user_id=user.id,
            facebook_user_id=13123123,
            action_domain='fashiolista:follow',
            content_type=love_content_type,
            object_id=user.id,
        )
        share.set_share_dict(kwargs)
        share.save()
        from open_facebook.exceptions import FacebookUnreachable
        with mock.patch('open_facebook.api.OpenFacebook') as mocked:
            instance = mocked.return_value
            instance.set = Mock(side_effect=FacebookUnreachable('broken'))
            share.send(graph=instance)
            self.assertEqual(share.error_message, 'broken')
            self.assertFalse(share.completed_at)


class UserConnectTest(FacebookTest):
    '''
    Tests the connect user functionality
    '''
    fixtures = ['users.json']

    def test_persistent_graph(self):
        request = RequestMock().get('/')
        request.session = {}
        request.user = AnonymousUser()

        graph = get_facebook_graph(access_token='short_username')
        FacebookUserConverter(graph)
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(action, CONNECT_ACTIONS.REGISTER)

    def test_gender_matching(self):
        request = RequestMock().get('/')
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

    def test_long_username(self):
        request = RequestMock().get('/')
        request.session = {}
        request.user = AnonymousUser()
        graph = get_persistent_graph(request, access_token='long_username')
        converter = FacebookUserConverter(graph)
        base_data = converter.facebook_registration_data()
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(len(base_data['username']), 30)
        self.assertEqual(len(user.username), 30)
        self.assertEqual(len(user.first_name), 30)
        self.assertEqual(len(user.last_name), 30)

    def test_full_connect(self):
        #going for a register, connect and login
        graph = get_facebook_graph(access_token='short_username')
        FacebookUserConverter(graph)
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(action, CONNECT_ACTIONS.REGISTER)
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(action, CONNECT_ACTIONS.LOGIN)
        self.request.GET._mutable = True
        self.request.GET['connect_facebook'] = 1
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(action, CONNECT_ACTIONS.CONNECT)
        self.request.user = AnonymousUser()
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(action, CONNECT_ACTIONS.LOGIN)

    def test_parallel_register(self):
        '''
        Adding some testing for the case when one person tries to register
        multiple times in the same second
        '''
        graph = get_facebook_graph(access_token='short_username')
        FacebookUserConverter(graph)
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(action, CONNECT_ACTIONS.REGISTER)

        self.request.user.is_authenticated = lambda: False
        with patch('django_facebook.connect.authenticate') as patched:
            return_sequence = [user, None]

            def side(*args, **kwargs):
                value = return_sequence.pop()
                return value

            patched.side_effect = side
            with patch('django_facebook.connect._register_user') as patched_register:
                patched_register.side_effect = facebook_exceptions.AlreadyRegistered('testing parallel registers')
                action, user = connect_user(self.request, facebook_graph=graph)
                self.assertEqual(action, CONNECT_ACTIONS.LOGIN)

    def test_utf8(self):
        graph = get_facebook_graph(access_token='unicode_string')
        facebook = FacebookUserConverter(graph)
        action, user = connect_user(self.request, facebook_graph=graph)

    def test_invalid_token(self):
        self.assertRaises(AssertionError,
                          connect_user, self.request, access_token='invalid')

    def test_no_email_registration(self):
        from django_facebook import exceptions as facebook_exceptions
        self.assertRaises(facebook_exceptions.IncompleteProfileError,
                          connect_user, self.request, access_token='no_email')

    def test_current_user(self):
        facebook = get_facebook_graph(access_token='tschellenbach')
        action, user = connect_user(self.request, facebook_graph=facebook)
        self.assertEqual(action, CONNECT_ACTIONS.LOGIN)

    def test_fb_update_required(self):
        def pre_update(sender, profile, facebook_data, **kwargs):
            profile.pre_update_signal = True

        Profile = get_profile_class()
        signals.facebook_pre_update.connect(pre_update, sender=Profile)
        facebook = get_facebook_graph(access_token='tschellenbach')

        facebook_settings.FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN = True
        action, user = connect_user(self.request, facebook_graph=facebook)
        self.assertEqual(action, CONNECT_ACTIONS.LOGIN)
        self.assertTrue(hasattr(user.get_profile(), 'pre_update_signal'))

        facebook_settings.FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN = False
        action, user = connect_user(self.request, facebook_graph=facebook)
        self.assertEqual(action, CONNECT_ACTIONS.LOGIN)
        self.assertFalse(hasattr(user.get_profile(), 'pre_update_signal'))

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

    def test_connect_page(self):
        url = reverse('facebook_connect')
        c = Client()
        response = c.get(url)
        self.assertEqual(response.status_code, 200)


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
        from open_facebook import exceptions as open_facebook_exceptions
        raise_something = partial(FacebookConnection.raise_error, 0,
                                  "(#200) The user hasn't authorized the "
                                  "application to perform this action")
        self.assertRaises(open_facebook_exceptions.PermissionException,
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
        signals.facebook_user_registered.connect(
            user_registered, sender=get_user_model())
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


def fake_connect(request, access_tokon, graph):
    return ('action', 'user')


class FacebookCanvasMiddlewareTest(FacebookTest):

    def setUp(self):
        super(FacebookCanvasMiddlewareTest, self).setUp()
        self.factory = RequestFactory()
        self.middleware = FacebookCanvasMiddleWare()
        self.session_middleware = SessionMiddleware()

    def get_canvas_url(self, data={}):
        request = self.factory.post('/', data)
        request.META['HTTP_REFERER'] = 'https://apps.facebook.com/canvas/'
        self.session_middleware.process_request(request)
        return request

    def test_referer(self):
        #test empty referer
        request = self.factory.get('/')
        self.assertIsNone(self.middleware.process_request(request))
        #test referer not facebook
        request = self.factory.get('/')
        request.META['HTTP_REFERER'] = 'https://localhost:8000/'
        self.assertIsNone(self.middleware.process_request(request))
        request = self.get_canvas_url()
        response = self.middleware.process_request(request)
        self.assertIsInstance(response, CanvasRedirect)

    def test_user_denied(self):
        request = self.factory.get('/?error_reason=user_denied&error=access_denied&error_description=The+user+denied+your+request.')
        request.META['HTTP_REFERER'] = 'https://apps.facebook.com/canvas/'
        response = self.middleware.process_request(request)
        self.assertIsInstance(response, CanvasRedirect)

    @patch.object(FacebookAuthorization, 'parse_signed_data')
    def test_non_auth_user(self, mocked_method=FacebookAuthorization.parse_signed_data):
        mocked_method.return_value = {}
        data = {'signed_request': 'dXairHLF8dfUKaL7ZFXaKmTsAglg0EkyHesTLnPcPAE.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImlzc3VlZF9hdCI6MTM1ODA2MTU1MSwidXNlciI6eyJjb3VudHJ5IjoiYnIiLCJsb2NhbGUiOiJlbl9VUyIsImFnZSI6eyJtaW4iOjIxfX19'}
        request = self.get_canvas_url(data=data)
        response = self.middleware.process_request(request)
        self.assertTrue(mocked_method.called)
        self.assertIsInstance(response, CanvasRedirect)

    @patch('django_facebook.middleware.connect_user', fake_connect)
    @patch.object(OpenFacebook, 'permissions')
    @patch.object(FacebookAuthorization, 'parse_signed_data')
    def test_auth_user(
        self, mocked_method_1=FacebookAuthorization.parse_signed_data,
            mocked_method_2=OpenFacebook.permissions):
        data = {'signed_request': 'd7JQQIfxHgEzLIqJMeU9J5IlLg7shzPJ8DFRF55L52w.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImV4cGlyZXMiOjEzNTgwNzQ4MDAsImlzc3VlZF9hdCI6MTM1ODA2ODU1MCwib2F1dGhfdG9rZW4iOiJBQUFGdk02MWpkT0FCQVBhWkNzR1pDM0dEVFZtdDJCWkFQVlpDc0F0aGNmdXBYUnhMN1cwUHBaQm53OEUwTzBBRVNYNjVaQ0JHdjZpOFRBWGhnMEpzbER5UmtmZUlnYnNHUmV2eHQxblFGZ0hNcFNpeTNWRTB3ZCIsInVzZXIiOnsiY291bnRyeSI6ImJyIiwibG9jYWxlIjoiZW5fVVMiLCJhZ2UiOnsibWluIjoyMX19LCJ1c2VyX2lkIjoiMTAwMDA1MDEyNDY2Nzg1In0'}
        request = self.get_canvas_url(data=data)
        request.user = AnonymousUser()
        mocked_method_1.return_value = {'user_id': '123456',
                                        'oauth_token': 'qwertyuiop'}
        mocked_method_2.return_value = facebook_settings.FACEBOOK_DEFAULT_SCOPE
        self.assertIsNone(self.middleware.process_request(request))
        self.assertTrue(mocked_method_1.called)

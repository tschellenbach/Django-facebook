from __future__ import with_statement
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.test.client import Client, RequestFactory
from django_facebook import exceptions as facebook_exceptions, \
    settings as facebook_settings, signals
from django_facebook.api import get_facebook_graph, FacebookUserConverter, \
    get_persistent_graph
from django_facebook.auth_backends import FacebookBackend
from django_facebook.connect import _register_user, connect_user, \
    CONNECT_ACTIONS
from django_facebook.middleware import FacebookCanvasMiddleWare
from django_facebook.test_utils.mocks import RequestMock
from django_facebook.test_utils.testcases import FacebookTest, LiveFacebookTest
from django_facebook.utils import cleanup_oauth_url, get_profile_model, \
    ScriptRedirect, get_user_model, get_user_attribute, try_get_profile, \
    get_instance_for_attribute, update_user_attributes
from functools import partial
from mock import Mock, patch
from open_facebook.api import FacebookConnection, FacebookAuthorization, \
    OpenFacebook
from open_facebook.exceptions import FacebookSSLError, FacebookURLError
import logging
import mock
from django.utils import unittest
from django_facebook.models import OpenGraphShare
from django.contrib.contenttypes.models import ContentType
from open_facebook.exceptions import FacebookUnreachable, OAuthException

logger = logging.getLogger(__name__)
__doctests__ = ['django_facebook.api']


class BaseDecoratorTest(FacebookTest):

    def setUp(self):
        FacebookTest.setUp(self)
        from django_facebook.decorators import facebook_required
        self.decorator = facebook_required
        self.decorator_name = 'FacebookRequired'

    def test_naming(self):
        self.assertEqual(self.decorator.__name__, self.decorator_name)

    def test_wrapping(self):
        '''
        Verify that the decorator wraps the original function
        '''

        @self.decorator
        def myfunc(request):
            '''docs'''
            pass
        self.assertEqual(myfunc.__doc__, 'docs')
        self.assertEqual(myfunc.__name__, 'myfunc')

        @self.decorator()
        def myfunc2(request):
            '''docs2'''
            pass
        self.assertEqual(myfunc2.__doc__, 'docs2')
        self.assertEqual(myfunc2.__name__, 'myfunc2')


class DecoratorTest(BaseDecoratorTest):

    '''
    Verify that the lazy and facebook_required decorator work as expected

    Facebook required decorator
        If you have the permissions proceed
        Else show the login screen
            If you allow, proceed
            If you click cancel ...

    Facebook required lazy
        Proceed
        Upon OAuthException, go to login screen
            If you allow proceed
            If you click cancel ...
    '''

    def setUp(self):
        BaseDecoratorTest.setUp(self)
        self.url = reverse('facebook_decorator_example')
        target_url = r'''https://www.facebook.com/dialog/oauth?scope=email%2Cuser_about_me%2Cuser_birt
            hday%2Cuser_website&redirect_uri=http%3A%2F%2Ftestserver%2Ffacebook%2Fdecorator_
            example%2F%3Fattempt%3D1&client_id=215464901804004
        '''.replace(' ', '').replace('\n', '')
        self.target_url = target_url
        from django_facebook.decorators import facebook_required
        self.decorator = facebook_required

    def test_decorator_not_authenticated(self):
        '''
        We should redirect to Facebook oauth dialog
        '''
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, self.target_url, target_status_code=404)

    def test_decorator_authenticated(self):
        '''
        Here we fake that we have permissions
        This should enter the view and in this test return "authorized"
        '''
        self.mock_authenticated()
        response = self.client.get(self.url, follow=True)
        self.assertEqual(response.content, 'authorized')

    def test_decorator_denied(self):
        '''
        Here the users denies our app. Facebook adds this in the url
        attempt=1&error_reason=user_denied&error=access_denied&error_description=The+user+denied+your+request.
        '''
        query_dict_string = 'attempt=1&error_reason=user_denied&error=access_denied&error_description=The+user+denied+your+request.'
        get = QueryDict(query_dict_string, True)
        denied_url = '%s?%s' % (self.url, get.urlencode())
        response = self.client.get(denied_url, follow=True)
        self.assertEqual(response.content, 'user denied or error')


class ScopedDecoratorTest(DecoratorTest):

    '''
    Tests the more complicated but faster lazy decorator
    '''

    def setUp(self):
        DecoratorTest.setUp(self)
        self.url = reverse('facebook_decorator_example_scope')
        target_url = r'https://www.facebook.com/dialog/oauth?scope=publish_actions%2Cuser_status&redirect_uri=http%3A%2F%2Ftestserver%2Ffacebook%2Fdecorator_example_scope%2F%3Fattempt%3D1&client_id=215464901804004'
        self.target_url = target_url

    def test_type_error(self):
        self.mock_authenticated()

        @self.decorator
        def myview(request, graph):
            def inner(a, b):
                pass
            inner(1, 2, c='nono')

        to_fail = partial(myview, self.request)
        try:
            to_fail()
        except TypeError, e:
            right_error = "inner() got an unexpected keyword argument 'c'"
            self.assertEqual(e.message, right_error)


class LazyDecoratorTest(DecoratorTest):

    '''
    Tests the more complicated but faster lazy decorator
    '''

    def setUp(self):
        DecoratorTest.setUp(self)
        self.url = reverse('facebook_lazy_decorator_example')
        target_url = r'''https://www.facebook.com/dialog/oauth?scope=email%2Cuser_about_me%2Cuser_birt
            hday%2Cuser_website&redirect_uri=http%3A%2F%2Ftestserver%2Ffacebook%2Flazy_decorator_
            example%2F%3Fattempt%3D1&client_id=215464901804004
        '''.replace(' ', '').replace('\n', '')
        self.target_url = target_url
        from django_facebook.decorators import facebook_required_lazy
        self.decorator = facebook_required_lazy
        self.decorator_name = 'FacebookRequiredLazy'


class GraphAccessTest(FacebookTest):

    def test_get_persistent(self):
        graph = get_persistent_graph(self.request)
        # fake that we are authenticated and have a facebook graph
        with patch.object(self.request, 'facebook'):
            self.request.user = get_user_model().objects.all()[:1][0]
            graph = get_persistent_graph(self.request)


class ConnectViewTest(FacebookTest):

    def setUp(self):
        FacebookTest.setUp(self)

        self.base_url = base_url = 'http://testserver'
        self.absolute_default_url = base_url + \
            facebook_settings.FACEBOOK_LOGIN_DEFAULT_REDIRECT
        self.url = reverse('facebook_connect')
        self.absolute_url = base_url + reverse('facebook_connect')
        self.example_url = reverse('facebook_example')
        self.absolute_example_url = base_url + reverse('facebook_example')

    def test_connect_redirect(self):
        '''
        The redirect flow for facebook works as follows

        - request the decorated url, /facebook/connect/
        - the decorator (facebook_required) redirect the user to the oauth url
        - after accepting the auth dialog facebook redirects us to the next url
        '''
        # STEP 1, verify that we redirect to facebook with the correct details
        response = self.client.post(
            self.url, next=self.example_url, follow=True)
        redirect_url = response.redirect_chain[0][0]
        oauth_url = 'https://www.facebook.com/dialog/oauth?scope=email%2Cuser_about_me%2Cuser_birthday%2Cuser_website&redirect_uri=http%3A%2F%2Ftestserver%2Ffacebook%2Fconnect%2F%3Fattempt%3D1&client_id=215464901804004'
        self.assertEqual(redirect_url, oauth_url)

    def test_connect_redirect_authenticated(self):
        # Meanwhile at Facebook they redirect the request
        # STEP 2 Authenticated, verify that the connect view redirects to the
        # example
        self.mock_authenticated()
        accepted_url = self.url + \
            '?attempt=1&client_id=215464901804004&next=bla&register_next=%s' % self.example_url
        response = self.client.get(accepted_url, follow=True)
        redirect_url = response.redirect_chain[0][0]
        self.assertEqual(redirect_url, self.absolute_example_url)

        # Verify that login_next works
        accepted_url = self.url + \
            '?attempt=1&client_id=215464901804004&next=bla&login_next=%s' % self.example_url
        response = self.client.get(accepted_url, follow=True)
        redirect_url = response.redirect_chain[0][0]
        self.assertEqual(redirect_url, self.absolute_example_url)

    def test_connect_redirect_default(self):
        # Now try without next
        self.mock_authenticated()
        accepted_url = self.url + '?attempt=1&client_id=215464901804004'
        response = self.client.get(accepted_url, follow=True)
        redirect_url = response.redirect_chain[0][0]
        self.assertEqual(redirect_url, self.absolute_default_url)

    def test_connect_redirect_not_authenticated(self):
        # Meanwhile at Facebook they redirect the request
        # STEP 2 Not Authenticated, verify that the connect view redirects to
        # the example
        accepted_url = self.url + \
            '?attempt=1&client_id=215464901804004&next=%s' % self.example_url
        response = self.client.get(accepted_url, follow=True)
        redirect_url = response.redirect_chain[0][0]
        error_url = self.absolute_example_url + '?fb_error_or_cancel=1'
        self.assertEqual(redirect_url, error_url)

        # Verify that error next also works
        accepted_url = self.url + \
            '?attempt=1&client_id=215464901804004&next=bla&error_next=%s' % self.example_url
        response = self.client.get(accepted_url, follow=True)
        redirect_url = response.redirect_chain[0][0]
        error_url = self.absolute_example_url + '?fb_error_or_cancel=1'
        self.assertEqual(redirect_url, error_url)

    def test_connect(self):
        '''
        Test if we can do logins
        django_facebook.connect.connect_user
        '''
        user = get_user_model().objects.all()[:1][0]
        url = self.url
        example_url = reverse('facebook_example')

        # test registration flow
        with patch('django_facebook.views.connect_user', return_value=(CONNECT_ACTIONS.REGISTER, user)) as wrapped_connect:
            post_data = dict(
                access_token='short_username',
                next='%s?register=1' % example_url,
            )
            response = self.client.post(url, post_data, follow=True)
            self.assertEqual(wrapped_connect.call_count, 1)
            self.assertIn('register', response.redirect_chain[0][0])
            self.assertEqual(response.status_code, 200)

        # user register next instead of next
        with patch('django_facebook.views.connect_user', return_value=(CONNECT_ACTIONS.REGISTER, user)) as wrapped_connect:
            post_data = dict(
                access_token='short_username',
                register_next='%s?register=1' % example_url
            )
            response = self.client.post(url, post_data, follow=True)
            self.assertEqual(wrapped_connect.call_count, 1)
            self.assertIn('register', response.redirect_chain[0][0])
            self.assertEqual(response.status_code, 200)

        # test login
        with patch('django_facebook.views.connect_user', return_value=(CONNECT_ACTIONS.LOGIN, user)) as wrapped_connect:
            post_data = dict(
                access_token='short_username',
                next='%s?loggggg=1' % example_url,
            )
            response = self.client.post(url, post_data, follow=True)
            self.assertEqual(wrapped_connect.call_count, 1)
            self.assertIn('?loggggg=1', response.redirect_chain[0][0])
            self.assertEqual(response.status_code, 200)

        # test connect
        with patch('django_facebook.views.connect_user', return_value=(CONNECT_ACTIONS.CONNECT, user)) as wrapped_connect:
            post_data = dict(
                access_token='short_username',
                next='%s?loggggg=1' % example_url
            )
            response = self.client.post(url, post_data, follow=True)
            self.assertEqual(wrapped_connect.call_count, 1)
            assert '?loggggg=1' in response.redirect_chain[0][0]
            self.assertEqual(response.status_code, 200)

        # test connect
        from django_facebook import exceptions as facebook_exceptions
        profile_error = facebook_exceptions.IncompleteProfileError()
        profile_error.form = None
        with patch('django_facebook.views.connect_user', return_value=(CONNECT_ACTIONS.REGISTER, user), side_effect=profile_error) as wrapped_connect:
            post_data = dict(access_token='short_username',
                             next='%s?loggggg=1' % example_url)
            response = self.client.post(url, post_data, follow=True)
            self.assertEqual(wrapped_connect.call_count, 1)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context)
            template = self.get_response_template(response)
            assert template.name in facebook_settings.FACEBOOK_REGISTRATION_TEMPLATE or template.name == facebook_settings.FACEBOOK_REGISTRATION_TEMPLATE

    def test_slow_connect(self):
        '''
        Test if we can do logins
        django_facebook.connect.connect_user
        '''
        url = reverse('facebook_connect')
        example_url = reverse('facebook_example')

        # test super slow Facebook
        errors = [FacebookSSLError(), FacebookURLError(
            '<urlopen error _ssl.c:489: The handshake operation timed out>')]
        for error in errors:
            with patch('django_facebook.views.get_instance_for') as converter:
                instance = converter.return_value
                instance.is_authenticated = Mock(side_effect=error)
                post_data = dict(
                    access_token='short_username',
                    next='%s?loggggg=1' % example_url
                )
                response = self.client.post(url, post_data, follow=True)
                self.assertEqual(instance.is_authenticated.call_count, 1)
                self.assertTrue(response.context)
                assert '?loggggg=1' in response.redirect_chain[0][0]

    def get_response_template(self, response):
        if hasattr(response, 'template'):
            templates = [response.template]
        else:
            templates = response.templates
        template = templates[0]
        return template


class TestUserTest(LiveFacebookTest):

    def test_create_test_user(self):
        # Also, somehow unittest.skip doesnt work with travis ci?
        return 'Skipping since you might have created test users manually, lets not delete them :)'
        # start by clearing out our test users (maybe this isnt safe to use in testing)
        # if other people create test users manualy this could be annoying
        app_access_token = FacebookAuthorization.get_cached_app_access_token()
        FacebookAuthorization.delete_test_users(app_access_token)
        # the permissions for which we want a test user
        permissions = ['email', 'publish_actions']
        # gets the test user object
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


class OpenGraphShareTest(FacebookTest):

    def setUp(self):
        FacebookTest.setUp(self)
        user_url = 'http://www.fashiolista.com/style/neni/'
        kwargs = dict(item=user_url)
        user = get_user_model().objects.all()[:1][0]
        profile = try_get_profile(user)
        user_or_profile = get_instance_for_attribute(
            user, profile, 'facebook_open_graph')
        user_or_profile.facebook_open_graph = True
        user_or_profile.save()

        some_content_type = ContentType.objects.all()[:1][0]
        share = OpenGraphShare.objects.create(
            user_id=user.id,
            facebook_user_id=13123123,
            action_domain='fashiolista:follow',
            content_type=some_content_type,
            object_id=user.id,
        )
        share.set_share_dict(kwargs)
        share.save()
        self.share = share
        self.share_details = user, profile, share

    def test_follow_og_share(self):
        user_url = 'http://www.fashiolista.com/style/neni/'
        kwargs = dict(item=user_url)
        user = get_user_model().objects.all()[:1][0]
        from django.contrib.contenttypes.models import ContentType
        some_content_type = ContentType.objects.all()[:1][0]
        share = OpenGraphShare.objects.create(
            user_id=user.id,
            facebook_user_id=13123123,
            action_domain='fashiolista:follow',
            content_type=some_content_type,
            object_id=user.id,
        )
        share.set_share_dict(kwargs)
        share.save()
        share.send()

    def test_follow_og_share_error(self):
        '''
        A normal OpenFacebook exception, shouldnt reset the new token required

        However an OAuthException should set new_token_required to True,
        But only if we are indeed failing has_permissions(['publish_actions'])
        '''
        # utility function for testing purposes
        def test_send(error, expected_error_message, expected_new_token, has_permissions=False):
            user, profile, share = self.share_details
            update_user_attributes(
                user, profile, dict(new_token_required=False), save=True)
            with mock.patch('open_facebook.api.OpenFacebook') as mocked:
                instance = mocked.return_value
                instance.set = Mock(side_effect=error)
                instance.has_permissions = Mock(return_value=has_permissions)
                instance.access_token = get_user_attribute(
                    user, profile, 'access_token')
                share.send(graph=instance)
                self.assertEqual(share.error_message, expected_error_message)
                self.assertFalse(share.completed_at)
                user = get_user_model().objects.get(id=user.id)
                if profile:
                    profile = get_profile_model().objects.get(id=profile.id)
                new_token_required = get_user_attribute(
                    user, profile, 'new_token_required')
                self.assertEqual(new_token_required, expected_new_token)

        # test with a basic exception, this should reset the new_token_required
        test_send(
            error=FacebookUnreachable('broken'),
            expected_error_message='FacebookUnreachable(\'broken\',)',
            expected_new_token=False,
            has_permissions=False,
        )
        # now try with an oAuthException and no permissions
        # this should set new_token_required to true
        test_send(
            error=OAuthException('permissions'),
            expected_error_message="OAuthException('permissions',)",
            expected_new_token=True,
            has_permissions=False,
        )
        # now an oAuthException, but we already have the permissions
        # this means we shouldnt set new_token_required to True
        test_send(
            error=OAuthException('permissions'),
            expected_error_message="OAuthException('permissions',)",
            expected_new_token=False,
            has_permissions=True,
        )


class UserConnectTest(FacebookTest):

    '''
    Tests the connect user functionality
    '''

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
        profile = try_get_profile(user)
        gender = get_user_attribute(user, profile, 'gender')
        self.assertEqual(gender, 'm')

    def test_update_access_token(self):
        request = RequestMock().get('/')
        request.session = {}
        request.user = AnonymousUser()
        graph = get_persistent_graph(request, access_token='paul')
        action, user = connect_user(self.request, facebook_graph=graph)
        first_user_id = user.id

        # new token required should start out as False
        profile = try_get_profile(user)
        new_token_required = get_user_attribute(
            user, profile, 'new_token_required')
        self.assertEqual(new_token_required, False)

        # we manually set it to true
        update_user_attributes(
            user, profile, dict(new_token_required=True), save=True)
        if profile:
            profile = get_profile_model().objects.get(id=profile.id)
        user = get_user_model().objects.get(id=user.id)
        new_token_required = get_user_attribute(
            user, profile, 'new_token_required')
        self.assertEqual(new_token_required, True)

        # another update should however set it back to False
        request.facebook = None
        graph = get_facebook_graph(request, access_token='paul2')
        logger.info('and the token is %s', graph.access_token)
        action, user = connect_user(self.request, facebook_graph=graph)
        user = get_user_model().objects.get(id=user.id)
        self.assertEqual(user.id, first_user_id)
        if profile:
            profile = get_profile_model().objects.get(id=profile.id)
        user = get_user_model().objects.get(id=user.id)
        new_token_required = get_user_attribute(
            user, profile, 'new_token_required')
        self.assertEqual(new_token_required, False)

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
        # going for a register, connect and login
        graph = get_facebook_graph(access_token='short_username')
        FacebookUserConverter(graph)
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(action, CONNECT_ACTIONS.REGISTER)
        # and now we do a login, not a connect
        action, user = connect_user(self.request, facebook_graph=graph)
        self.assertEqual(action, CONNECT_ACTIONS.LOGIN)
        self.request.GET._mutable = True
        self.request.GET['connect_facebook'] = 1
        action, user = connect_user(
            self.request, facebook_graph=graph, connect_facebook=True)
        self.assertEqual(action, CONNECT_ACTIONS.CONNECT)
        self.request.user = AnonymousUser()
        action, user = connect_user(
            self.request, facebook_graph=graph, connect_facebook=True)
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
                patched_register.side_effect = facebook_exceptions.AlreadyRegistered(
                    'testing parallel registers')
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
        def pre_update(sender, user, profile, facebook_data, **kwargs):
            user.pre_update_signal = True

        Profile = get_profile_model()
        user_model = get_user_model()
        signals.facebook_pre_update.connect(pre_update, sender=user_model)
        facebook = get_facebook_graph(access_token='tschellenbach')

        facebook_settings.FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN = True
        action, user = connect_user(self.request, facebook_graph=facebook)
        self.assertEqual(action, CONNECT_ACTIONS.LOGIN)
        self.assertTrue(hasattr(user, 'pre_update_signal'))

        facebook_settings.FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN = False
        action, user = connect_user(self.request, facebook_graph=facebook)
        self.assertEqual(action, CONNECT_ACTIONS.LOGIN)
        self.assertFalse(hasattr(user, 'pre_update_signal'))

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
        from django.conf import settings
        if settings.MODE == 'userena':
            return

        test_form = 'django_facebook.test_utils.forms.SignupForm'
        old_setting = facebook_settings.FACEBOOK_REGISTRATION_FORM
        facebook_settings.FACEBOOK_REGISTRATION_FORM = test_form
        try:
            facebook = get_facebook_graph(access_token='short_username')
            action, user = connect_user(self.request, facebook_graph=facebook)
            # The test form always sets username to test form
            self.assertEqual(user.username, 'Test form')
        finally:
            facebook_settings.FACEBOOK_REGISTRATION_FORM = old_setting


class SimpleRegisterViewTest(FacebookTest):

    '''
    Even the most simple views will break eventually if they are not tested
    '''

    def test_registration(self):
        pw = 'tester1234'
        data = dict(username='testertester', email='tester@testertester.com',
                    password1=pw, password2=pw)
        data['register_next'] = '/?a=bbbbcbbbb'
        response = self.client.post('/accounts/register/', data, follow=True)

        assert response.redirect_chain, 'we are expecting a redirect!'
        for url, status in response.redirect_chain:
            if 'bbbbcbbbb' in url:
                break
        else:
            raise ValueError('bbbbcbbbb isnt in %s' % response.redirect_chain)


class AuthBackend(FacebookTest):

    def test_auth_backend(self):
        # the auth backend
        backend = FacebookBackend()
        facebook = get_facebook_graph(access_token='new_user')
        action, user = connect_user(self.request, facebook_graph=facebook)
        facebook_email = user.email
        profile = try_get_profile(user)
        user_or_profile = get_instance_for_attribute(
            user, profile, 'facebook_id')
        facebook_id = user_or_profile.facebook_id
        auth_user = backend.authenticate(facebook_email=facebook_email)
        logger.info('%s %s %s', auth_user.email, user.email, facebook_email)
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

        def pre_update(sender, user, profile, facebook_data, **kwargs):
            user.pre_update_signal = True

        def post_update(sender, user, profile, facebook_data, **kwargs):
            user.post_update_signal = True

        Profile = get_profile_model()
        user_model = get_user_model()
        signals.facebook_user_registered.connect(
            user_registered, sender=user_model)
        signals.facebook_pre_update.connect(pre_update, sender=user_model)
        signals.facebook_post_update.connect(post_update, sender=user_model)

        graph = get_facebook_graph(access_token='short_username')
        facebook = FacebookUserConverter(graph)
        user = _register_user(self.request, facebook)
        self.assertEqual(hasattr(user, 'registered_signal'), True)
        self.assertEqual(hasattr(user, 'pre_update_signal'), True)
        self.assertEqual(hasattr(user, 'post_update_signal'), True)


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
        # test empty referer
        request = self.factory.get('/')
        self.assertIsNone(self.middleware.process_request(request))
        # test referer not facebook
        request = self.factory.get('/')
        request.META['HTTP_REFERER'] = 'https://localhost:8000/'
        self.assertIsNone(self.middleware.process_request(request))
        request = self.get_canvas_url()
        response = self.middleware.process_request(request)
        self.assertIsInstance(response, ScriptRedirect)

    def test_user_denied(self):
        request = self.factory.get(
            '/?error_reason=user_denied&error=access_denied&error_description=The+user+denied+your+request.')
        request.META['HTTP_REFERER'] = 'https://apps.facebook.com/canvas/'
        response = self.middleware.process_request(request)
        self.assertIsInstance(response, ScriptRedirect)

    @patch.object(FacebookAuthorization, 'parse_signed_data')
    def test_non_auth_user(self, mocked_method=FacebookAuthorization.parse_signed_data):
        mocked_method.return_value = {}
        data = {'signed_request':
                'dXairHLF8dfUKaL7ZFXaKmTsAglg0EkyHesTLnPcPAE.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImlzc3VlZF9hdCI6MTM1ODA2MTU1MSwidXNlciI6eyJjb3VudHJ5IjoiYnIiLCJsb2NhbGUiOiJlbl9VUyIsImFnZSI6eyJtaW4iOjIxfX19'}
        request = self.get_canvas_url(data=data)
        response = self.middleware.process_request(request)
        self.assertTrue(mocked_method.called)
        self.assertIsInstance(response, ScriptRedirect)

    @patch('django_facebook.middleware.connect_user', fake_connect)
    @patch.object(OpenFacebook, 'permissions')
    @patch.object(FacebookAuthorization, 'parse_signed_data')
    def test_auth_user(
        self, mocked_method_1=FacebookAuthorization.parse_signed_data,
            mocked_method_2=OpenFacebook.permissions):
        data = {'signed_request':
                'd7JQQIfxHgEzLIqJMeU9J5IlLg7shzPJ8DFRF55L52w.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImV4cGlyZXMiOjEzNTgwNzQ4MDAsImlzc3VlZF9hdCI6MTM1ODA2ODU1MCwib2F1dGhfdG9rZW4iOiJBQUFGdk02MWpkT0FCQVBhWkNzR1pDM0dEVFZtdDJCWkFQVlpDc0F0aGNmdXBYUnhMN1cwUHBaQm53OEUwTzBBRVNYNjVaQ0JHdjZpOFRBWGhnMEpzbER5UmtmZUlnYnNHUmV2eHQxblFGZ0hNcFNpeTNWRTB3ZCIsInVzZXIiOnsiY291bnRyeSI6ImJyIiwibG9jYWxlIjoiZW5fVVMiLCJhZ2UiOnsibWluIjoyMX19LCJ1c2VyX2lkIjoiMTAwMDA1MDEyNDY2Nzg1In0'}
        request = self.get_canvas_url(data=data)
        request.user = AnonymousUser()
        mocked_method_1.return_value = {'user_id': '123456',
                                        'oauth_token': 'qwertyuiop'}
        mocked_method_2.return_value = facebook_settings.FACEBOOK_DEFAULT_SCOPE
        self.assertIsNone(self.middleware.process_request(request))
        self.assertTrue(mocked_method_1.called)

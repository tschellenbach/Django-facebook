# -*- coding: utf-8 -*-

from open_facebook.api import *
import unittest
import logging
import mock
import datetime
from open_facebook.exceptions import OpenGraphException
logger = logging.getLogger()
from open_facebook.utils import json


TEST_USER_FORCE_CREATE = False
TEST_USER_DICT = {
    'tommy': dict(name='Tommaso Ilgubrab'),
    'thi': dict(name='Thierry Hcabnellehcs'),
    'guy': dict(name='Guyon Eerom', permissions=['read_stream'])
}
TEST_USER_NAMES = [v['name'] for k, v in TEST_USER_DICT.items()]

TEST_USER_OBJECTS = None


def setup_users():
    '''
    Since this is soo slow we only do this once for all tests
    '''
    # caching because these apis are just too damn slow for test driven
    # development
    from django.core.cache import cache
    global TEST_USER_OBJECTS
    if TEST_USER_OBJECTS is None:
        key = 'test_user_objects'
        user_objects = cache.get(key)
        if not user_objects or TEST_USER_FORCE_CREATE:
            logger.info('test user cache not found, rebuilding')
            user_objects = {}
            app_token = FacebookAuthorization.get_app_access_token()
            for user_slug, user_dict in TEST_USER_DICT.items():
                test_user = FacebookAuthorization.get_or_create_test_user(
                    app_token, name=user_dict[
                        'name'], force_create=TEST_USER_FORCE_CREATE,
                    permissions=user_dict.get('permissions')
                )
                user_objects[user_slug] = test_user
            cache.set(key, user_objects, 60 * 60)
        TEST_USER_OBJECTS = user_objects
    return TEST_USER_OBJECTS


class OpenFacebookTest(unittest.TestCase):

    def setUp(self):
        setup_users()
        for user_slug, user_object in TEST_USER_OBJECTS.items():
            setattr(self, user_slug, user_object)

        # capture print statements
        import sys
        import StringIO
        self.prints = sys.stdout = StringIO.StringIO()

    def tearDown(self):
        # complain about print statements
        self.prints.seek(0)
        content = self.prints.read()
        if content:
            raise ValueError('print statement found, output %s' % content)


class TestErrorMapping(OpenFacebookTest):

    def test_syntax_error(self):
        error_response = '''
        {
           'error': {
               'message': 'Syntax error "Expected end of string instead of "?"." at character 14: third_party_id?access_token=AAABbPDnY390BAOZA22ugLfCyr2OGH0k82VJMPJRR8qxceV96nBra53R5ISiou7VOD9eBd21ZCzPZC5Vn1hWbVkY9Qvx9g8wl1NCmuL9vwZDZD',
               'code': 2500,
               'type': 'OAuthException'
           }
        }
        '''
        return

    def test_oauth_errors(self):
        expires_response = '''{
          "error": {
            "type": "OAuthException",
            "message": "Session has expired at unix time SOME_TIME. The current unix time is SOME_TIME."
          }
        } '''
        changed_password_response = '''
        {
          "error": {
            "type": "OAuthException",
            "message": "The session has been invalidated because the user has changed the password."
          }
        }
        '''
        deauthorized_response = '''
        {
          "error": {
            "type": "OAuthException",
            "message": "Error validating access token: USER_ID has not authorized application APP_ID"
          }
        }
        '''
        loggedout_response = '''
        {
          "error": {
            "type": "OAuthException",
            "message": "Error validating access token: The session is invalid because the user logged out."
           }
        }
        '''
        responses = [expires_response, changed_password_response,
                     deauthorized_response, loggedout_response]
        response_objects = []
        for response_string in responses:
            response = json.loads(response_string)

            response_objects.append(response)

        from open_facebook import exceptions as open_facebook_exceptions
        for response in response_objects:
            oauth = False
            try:
                FacebookConnection.raise_error(response['error']['type'],
                                               response['error']['message'])
            except open_facebook_exceptions.OAuthException, e:
                oauth = True
            assert oauth, 'response %s didnt raise oauth error' % response

    def test_non_oauth_errors(self):
        object_open_graph_error = '''
        {"error":
            {"message": "(#3502) Object at URL http://www.fashiolista.com/my_style/list/441276/?og=active&utm_campaign=facebook_action_comment&utm_medium=facebook&utm_source=facebook has og:type of 'website'. The property 'list' requires an object of og:type 'fashiolista:list'. ",
            "code": 3502, "type": "OAuthException"
            }
        }
        '''
        response = json.loads(object_open_graph_error)

        def test():
            FacebookConnection.raise_error(
                response['error']['type'],
                response['error']['message'],
                response['error'].get('code')
            )
        self.assertRaises(OpenGraphException, test)


class Test500Detection(OpenFacebookTest):

    def test_application_error(self):
        '''
        Facebook errors often look like 500s
        Its a silly system, but we need to support it
        This is actually an application error

        '''
        from StringIO import StringIO
        graph = self.guy.graph()

        with mock.patch('urllib2.build_opener') as patched:
            from urllib2 import HTTPError

            opener = mock.MagicMock()
            response = StringIO('''{
              "error": {
                "type": "OAuthException",
                "message": "Error validating access token: USER_ID has not authorized application APP_ID"
              }
            }''')
            opener.open.side_effect = HTTPError(
                'bla', 500, 'bla', 'bla', response)

            patched.return_value = opener

            def make_request():
                graph.get('me')

            self.assertRaises(facebook_exceptions.OAuthException, make_request)

    def test_facebook_down(self):
        '''
        Facebook errors often look like 500s

        After 3 attempts while facebook is down we raise a FacebookUnreachable
        Exception

        '''
        from StringIO import StringIO
        graph = self.guy.graph()

        with mock.patch('urllib2.build_opener') as patched:
            from urllib2 import HTTPError

            opener = mock.MagicMock()

            def side_effect(*args, **kwargs):
                response = StringIO(u'''
                <title>Facebook | Error</title>
                Sorry, something went wrong.
                ''')
                http_exception = HTTPError('bla', 505, 'bla', 'bla', response)
                raise http_exception

            opener.open.side_effect = side_effect

            patched.return_value = opener

            def make_request():
                graph.get('me')

            self.assertRaises(
                facebook_exceptions.FacebookUnreachable, make_request)


class TestPublishing(OpenFacebookTest):

    def test_permissions(self):
        graph = self.thi.graph()
        permission_responses = [
            (
                {u'paging': {u'next': u'https://graph.facebook.com/100005270323705/permissions?access_token=CAADD9tTuZCZBQBALXBfM0xDzsn68jAS8HgUSnbhRkZAp5L1FFpY7iLu3aAytCv8jGN4ZCXZAbZCehSvnK7e8d9P22FZCeHarRnFbFne8MluM0S7UNhoCwKWBNrazrs2tjZCIelQAdzesschwzUr3kRCR0oL9bW4Tp6syWmjm0FOUjwZDZD&limit=5000&offset=5000'}, u'data': [
                    {u'user_photos': 1, u'publish_actions': 1, u'read_stream': 1, u'video_upload': 1, u'installed': 1, u'offline_access': 1, u'create_note': 1, u'publish_stream': 1, u'photo_upload': 1, u'share_item': 1, u'status_update': 1}]},
                {u'user_photos': True, u'publish_actions': True, u'read_stream': True, u'video_upload': True, u'installed': True, u'offline_access': True, u'create_note': True, u'publish_stream': True, u'photo_upload': True, u'share_item': True, u'status_update': True}),
            (
                {u'paging': {
                    u'next': u'https://graph.facebook.com/100005270323705/permissions?access_token=CAADD9tTuZCZBQBALXBfM0xDzsn68jAS8HgUSnbhRkZAp5L1FFpY7iLu3aAytCv8jGN4ZCXZAbZCehSvnK7e8d9P22FZCeHarRnFbFne8MluM0S7UNhoCwKWBNrazrs2tjZCIelQAdzesschwzUr3kRCR0oL9bW4Tp6syWmjm0FOUjwZDZD&limit=5000&offset=5000'}, u'data': []},
                {}),
        ]
        # test the full flow, just check no errors are raised
        live_permissions = graph.permissions()
        # test weird responses
        for response, correct_permissions in permission_responses:
            with mock.patch('open_facebook.api.OpenFacebook.get') as g:
                g.return_value = response
                permissions = graph.permissions()
                self.assertEqual(permissions, correct_permissions)

    def test_wallpost(self):
        graph = self.thi.graph()
        now = datetime.datetime.now()
        result = graph.set('me/feed', message='This should work %s' % now)
        self.assertTrue(result['id'])
        graph.delete(result['id'])

        # we have no permissions, this should fail
        guy_graph = self.guy.graph()
        try:
            guy_graph.set('me/feed', message='Nonnonono')
            raise ValueError('We were expecting a permissions exception')
        except facebook_exceptions.PermissionException, e:
            pass

    def test_og_follow(self):
        return
        # perform an og follow
        graph = self.thi.graph()
        path = 'me/og.follows'
        result = graph.set(path, profile=self.guy.id)
        self.assertTrue(result['id'])

        # now try removing it
        remove_path = result['id']
        deleted = graph.delete(remove_path)

    def test_og_adjust(self):
        return
        # perform an og follow
        graph = self.thi.graph()
        path = 'me/og.follows'
        result = graph.set(path, profile=self.guy.id)
        self.assertTrue(result['id'])

        change_result = graph.set(result['id'], message='hello world')
        assert change_result is True

    def test_og_explicit_share(self):
        return
        # perform an og follow
        graph = self.thi.graph()
        path = 'me/og.follows'
        result = graph.set(
            path, profile=self.guy.id, fb__explicitly_shared='true')
        self.assertTrue(result['id'])


class TestOpenFacebook(OpenFacebookTest):

    def test_cookie_parsing(self):
        cookie = 'F7cndfQuSIkcVHWIgg_SHQ4LIDJXeeHhiXUNjesOw5g.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImNvZGUiOiJVMTZuMFNoWVUxSTJ5VEFJMVZ0RmlvZTdhRVRaaEZ4cGV5d1hwYnZvOUprLmV5SnBkaUk2SW1OcmFGVXlWR053ZDA1VlMwSTRlUzFzZDA1WmFtY2lmUS5rZl9RTUhCMnVFTVh5YW83UU5UcnFGMlJzOGxxQUxrM1AxYm8zazBLMm5YUXpOZW5LSVlfczBVV3ZNbE1jTXAzcE04TXNLNVVDQUpjWlQ1N1ZaZXFkS3ZPeXRFbmdoODFxTmczTXVDeTBHNjB6WjFBOWZGZlpHenVDejdKSEVSSCIsImlzc3VlZF9hdCI6MTMxMTYwMDEyNywidXNlcl9pZCI6Nzg0Nzg1NDMwfQ'
        parsed_cookie = FacebookAuthorization.parse_signed_data(cookie)
        assert 'code' in parsed_cookie

    def test_code_conversion(self):
        from open_facebook import exceptions as open_facebook_exceptions
        # before testing update this with a valid code, hope facebook comes
        # with a way to automate this
        code = 'AQDByzD95HCaQLIY3PyQFvCJ67bkYx5f692TylEXARQ0p6_XK0mXGRVBU3G759qOIa_A966Wmm-kxxw1GbXkXQiJj0A3b_XNFewFhT8GSro4i9F8b_7q1RSnKzfq327XYno-Qw4NGxm0ordSl0gJ0YTjhwY8TwSMy2b2whD5ZhHvaYkEaC1J-GcBhkF7o4F2-W8'
        # the redirect uri needs to be connected
        try:
            user_token = FacebookAuthorization.convert_code(
                code, redirect_uri='http://local.mellowmorning.com:8080')
            facebook = OpenFacebook(user_token['access_token'])
            facebook.me()
        except open_facebook_exceptions.ParameterException, e:
            pass

    def test_fql(self):
        facebook = self.thi.graph()
        result = facebook.fql('SELECT name FROM user WHERE uid = me()')
        assert 'name' in result[0]

    def test_open_api(self):
        facebook = self.guy.graph()
        assert 'name' in facebook.me()
        assert facebook.get('fashiolista')

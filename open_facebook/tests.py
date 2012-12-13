# -*- coding: utf-8 -*-

from open_facebook.api import *
import unittest
import logging
logger = logging.getLogger()
from open_facebook.utils import json


TEST_USER_FORCE_CREATE = True
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
    #caching because these apis are just too damn slow for test driven development
    from django.core.cache import cache
    global TEST_USER_OBJECTS
    if TEST_USER_OBJECTS is None:
        user_objects = cache.get('test_user_objects')
        if not user_objects:
            user_objects = {}
            app_token = FacebookAuthorization.get_app_access_token()
            for user_slug, user_dict in TEST_USER_DICT.items():
                test_user = FacebookAuthorization.get_or_create_test_user(
                    app_token, name=user_dict[
                        'name'], force_create=TEST_USER_FORCE_CREATE,
                    permissions=user_dict.get('permissions')
                )
                user_objects[user_slug] = test_user
            cache.set('test_user_objects', user_objects, 60 * 5)
        TEST_USER_OBJECTS = user_objects
    return TEST_USER_OBJECTS


class OpenFacebookTest(unittest.TestCase):
    def setUp(self):
        setup_users()
        for user_slug, user_object in TEST_USER_OBJECTS.items():
            setattr(self, user_slug, user_object)


class TestErrorMapping(OpenFacebookTest):

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


class TestPublishing(OpenFacebookTest):
    def test_wallpost(self):
        graph = self.thi.graph()
        result = graph.set('me/feed', message='This should work')
        self.assertTrue(result['id'])

        #we have no permissions, this should fail
        guy_graph = self.guy.graph()
        try:
            guy_graph.set('me/feed', message='Nonnonono')
            raise ValueError('We were expecting a permissions exception')
        except facebook_exceptions.PermissionException, e:
            pass

    def test_og_follow(self):
        #perform an og follow
        graph = self.thi.graph()
        path = 'me/og.follows'
        result = graph.set(path, profile=self.guy.id)
        self.assertTrue(result['id'])

        #now try removing it
        remove_path = result['id']
        deleted = graph.delete(remove_path)


class TestOpenFacebook(OpenFacebookTest):
    def test_cookie_parsing(self):
        cookie = 'F7cndfQuSIkcVHWIgg_SHQ4LIDJXeeHhiXUNjesOw5g.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImNvZGUiOiJVMTZuMFNoWVUxSTJ5VEFJMVZ0RmlvZTdhRVRaaEZ4cGV5d1hwYnZvOUprLmV5SnBkaUk2SW1OcmFGVXlWR053ZDA1VlMwSTRlUzFzZDA1WmFtY2lmUS5rZl9RTUhCMnVFTVh5YW83UU5UcnFGMlJzOGxxQUxrM1AxYm8zazBLMm5YUXpOZW5LSVlfczBVV3ZNbE1jTXAzcE04TXNLNVVDQUpjWlQ1N1ZaZXFkS3ZPeXRFbmdoODFxTmczTXVDeTBHNjB6WjFBOWZGZlpHenVDejdKSEVSSCIsImlzc3VlZF9hdCI6MTMxMTYwMDEyNywidXNlcl9pZCI6Nzg0Nzg1NDMwfQ'
        parsed_cookie = FacebookAuthorization.parse_signed_data(cookie)
        assert 'code' in parsed_cookie

    def test_code_conversion(self):
        from open_facebook import exceptions as open_facebook_exceptions
        # before testing update this with a valid code, hope facebook comes with a way to automate this
        code = 'AQDByzD95HCaQLIY3PyQFvCJ67bkYx5f692TylEXARQ0p6_XK0mXGRVBU3G759qOIa_A966Wmm-kxxw1GbXkXQiJj0A3b_XNFewFhT8GSro4i9F8b_7q1RSnKzfq327XYno-Qw4NGxm0ordSl0gJ0YTjhwY8TwSMy2b2whD5ZhHvaYkEaC1J-GcBhkF7o4F2-W8'
        #the redirect uri needs to be connected
        try:
            user_token = FacebookAuthorization.convert_code(
                code, redirect_uri='http://local.mellowmorning.com:8080')
            facebook = OpenFacebook(user_token['access_token'])
            facebook.me()
        except open_facebook_exceptions.OAuthException, e:
            pass

    def test_fql(self):
        facebook = self.thi.graph()
        result = facebook.fql('SELECT name FROM user WHERE uid = me()')
        assert 'name' in result[0]

    def test_open_api(self):
        facebook = self.guy.graph()
        assert 'name' in facebook.me()
        assert facebook.get('fashiolista')

    def test_album_upload(self):
        facebook = self.tommy.graph()
        photo_urls = [
            'http://d.fashiocdn.com/images/entities/0/6/t/p/d/0.365x365.jpg',
            'http://e.fashiocdn.com/images/entities/0/5/E/b/Q/0.365x365.jpg',
        ]
        #feed method
        for photo in photo_urls:
            facebook.set(
                'me/feed', message='Fashiolista is awesome - part one',
                picture=photo)

        #app album method
        #gives an unknown error for some reason
#        for photo in photo_urls:
#            uploaded = facebook.set('me/photos', url=photo, message='Fashiolista 2 is awesome - part two', name='FashiolistaTest2')
        albums = facebook.get('me/albums')
        album_names = [album['name'] for album in albums['data']]

        album_name = 'FashiolistaSuperAlbum'
        album_response = facebook.set('me/albums', params=dict(
            name=album_name, message='Your latest fashion finds'))

        albums = facebook.get('me/albums')
        album_names = [album['name'] for album in albums['data']]
        assert album_name in album_names

        album_id = album_response['id']
        for photo in photo_urls:
            facebook.set(
                '%s/photos' % album_id, url=photo,
                message='the writing is one the wall tw',
                name='FashiolistaTestt')

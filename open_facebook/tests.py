import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'facebook_example.settings'
from open_facebook.api import *
import unittest
import logging
logger = logging.getLogger()


class TestOpenFacebook(unittest.TestCase):
    def test_thijs_profile(self):

        token = FacebookAuthorization.get_app_access_token()
        FacebookAuthorization.create_test_user(token)
        test_user = FacebookAuthorization.get_or_create_test_user(token)
        return

        message = "Hi! I'm on Fashiolista, a worldwide community for " \
                  "fashion inspiration. Click to see my style profile and " \
                  "discover great new shops and fashion items!"
        image_urls = [
            'http://e.fashiocdn.com/images/entities/0/0/x/l/W/0.365x365.jpg',
            'http://d.fashiocdn.com/images/entities/0/9/9/j/j/0.365x365.jpg',
            'http://e.fashiocdn.com/images/entities/0/8/0/7/4/0.365x365.jpg',
        ]
        token = None
        access_token = '215464901804004|fc589819a12431167c3bd571.0-100002862180253|by58p1KHqf_XiqA4ux390XBGBIo'
        # login
        # https://www.facebook.com/platform/test_account_login.php?user_id=100002898600225&n=I4x8lGXREnEhea7
        # fill in a real token for this to work
        # {u'access_token': u'215464901804004|fc589819a12431167c3bd571.0-100002862180253|by58p1KHqf_XiqA4ux390XBGBIo', u'password': u'1439799010', u'login_url': u'https://www.facebook.com/platform/test_account_login.php?user_id=100002862180253&n=4xdwSTQbstgOzUt', u'id': u'100002862180253', u'email': u'hello_edztofa_world@tfbnw.net'}
        fb = OpenFacebook(access_token)
        print fb.get('me/accounts')
        return
        permissions = [p for p, v in fb.get(
            'me/permissions')['data'][0].items() if v]
        print permissions
        return
        print fb.fql("SELECT uid, name, sex FROM user WHERE uid IN " \
                     "(SELECT uid2 FROM friend WHERE uid1 = me())")
        return
        actions = [dict(name='Follow', link='http://www.fashiolista.com/')]
        # print fb.get('thijsgoos', metadata='1')['metadata']
        types = ['link', 'photo']

        for type in types:
            for image_url in image_urls:
                fb.set('me/feed', picture=image_url,
                       actions=actions, type=type, message=type)
        # print fb.set('696010430_10150752137065431/likes')

    def test_app_access_token(self):
        token = FacebookAuthorization.get_app_access_token()
        test_user = FacebookAuthorization.create_test_user(token)
        token_available = 'access_token' in test_user
        assert token_available, 'App authentication failed %s' % test_user

    def test_cookie_parsing(self):
        cookie = 'F7cndfQuSIkcVHWIgg_SHQ4LIDJXeeHhiXUNjesOw5g.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImNvZGUiOiJVMTZuMFNoWVUxSTJ5VEFJMVZ0RmlvZTdhRVRaaEZ4cGV5d1hwYnZvOUprLmV5SnBkaUk2SW1OcmFGVXlWR053ZDA1VlMwSTRlUzFzZDA1WmFtY2lmUS5rZl9RTUhCMnVFTVh5YW83UU5UcnFGMlJzOGxxQUxrM1AxYm8zazBLMm5YUXpOZW5LSVlfczBVV3ZNbE1jTXAzcE04TXNLNVVDQUpjWlQ1N1ZaZXFkS3ZPeXRFbmdoODFxTmczTXVDeTBHNjB6WjFBOWZGZlpHenVDejdKSEVSSCIsImlzc3VlZF9hdCI6MTMxMTYwMDEyNywidXNlcl9pZCI6Nzg0Nzg1NDMwfQ'
        parsed_cookie = FacebookAuthorization.parse_signed_data(cookie)
        assert 'code' in parsed_cookie

    def test_code_conversion(self):
        # before testing update this with a valid code, hope facebook comes with a way to automate this
        code = 'AQDByzD95HCaQLIY3PyQFvCJ67bkYx5f692TylEXARQ0p6_XK0mXGRVBU3G759qOIa_A966Wmm-kxxw1GbXkXQiJj0A3b_XNFewFhT8GSro4i9F8b_7q1RSnKzfq327XYno-Qw4NGxm0ordSl0gJ0YTjhwY8TwSMy2b2whD5ZhHvaYkEaC1J-GcBhkF7o4F2-W8'
        #the redirect uri needs to be connected
        user_token = FacebookAuthorization.convert_code(
            code, redirect_uri='http://local.mellowmorning.com:8080')
        facebook = OpenFacebook(user_token['access_token'])
        facebook.me()

    def test_fql(self):
        token = self.get_access_token()
        facebook = OpenFacebook(token)
        result = facebook.fql('SELECT name FROM user WHERE uid = me()')
        assert 'name' in result[0]

    def get_access_token(self):
        token = FacebookAuthorization.get_app_access_token()
        test_user = FacebookAuthorization.create_test_user(token)
        return test_user['access_token']

    def test_open_api(self):
        token = self.get_access_token()
        facebook = OpenFacebook(token)
        assert 'name' in facebook.me()

        assert facebook.get('fashiolista')

    def test_album_upload(self):
        token = self.get_access_token()
        facebook = OpenFacebook(token)
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


if __name__ == '__main__':
    import logging
    handler = logging.StreamHandler()
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    unittest.main(defaultTest='TestOpenFacebook.test_thijs_profile')

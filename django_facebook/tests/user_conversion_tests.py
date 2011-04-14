from __future__ import with_statement

import unittest

import os, sys
from django_facebook import exceptions as facebook_exceptions
os.environ['ENVIRONMENT'] = 'testing'
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.conf import settings
from django.test.client import Client, RequestFactory 
from django.contrib.auth.models import AnonymousUser
from django_facebook.connect import connect_user

import logging
logger = logging.getLogger(__name__)

class FacebookTest(unittest.TestCase):
    def setUp(self):
        from django_facebook import api
        from django_facebook.tests.mock_official_sdk import MockFacebookAPI
        api.FacebookAPI = MockFacebookAPI
        rf = RequestFactory()
        self.request = request = rf.get('/')
        request.user = AnonymousUser()
        from django.contrib.sessions.models import Session
        session = Session()
        request.session = session.get_decoded()
        print request.session
    
    
class UserConnectTest(FacebookTest):
    fixtures = ['mine']
    
    def test_invalid_token(self):
        self.assertRaises(AssertionError, connect_user, self.request, access_token='invalid')

    def test_no_email_registration(self):
        self.assertRaises(facebook_exceptions.IncompleteProfileError, connect_user, self.request, access_token='no_email')
    
    def test_current_user(self):
        self.assertRaises(facebook_exceptions.IncompleteProfileError, connect_user, self.request, access_token='tschellenbach')
    
    def test_new_user(self):
        self.assertRaises(facebook_exceptions.IncompleteProfileError, connect_user, self.request, access_token='new_user')
    
    
    
    
    
    
    
    
    
    
    
    
    
#    def test_doctest_api(self):
#        from django_facebook import api
#        import doctest
#        doctest.testmod(api)
#
#    def test_no_birthday(self):
#        facebook_data = test_users['no_birthday']
#        django_user_data = FacebookAPI._convert_facebook_data(facebook_data)
#        django_user_data_valid = {'website': 'www.pytell.com', 'username': u'jpytell', 'first_name': 'Jonathan', 'last_name': 'Pytell', 'verified': True, 'name': 'Jonathan Pytell', 'image': 'http://graph.facebook.com/me/picture?type=large', 'facebook_id': '776872663', 'about_me': None, 'updated_time': '2010-01-01T18:13:17+0000', 'date_of_birth': None, 'facebook_name': 'Jonathan Pytell', 'link': 'http://www.facebook.com/jpytell', 'location': {'id': None, 'name': None}, 'timezone':-4, 'image_thumb': 'http://graph.facebook.com/me/picture', 'facebook_profile_url': 'http://www.facebook.com/jpytell', 'id': '776872663', 'website_url': u'http://www.pytell.com/'}
#        self.assertEqualUserData(django_user_data, django_user_data_valid)
#
#    def test_partial_birthday(self):
#        facebook_data = test_users['partial_birthday']
#        django_user_data = FacebookAPI._convert_facebook_data(facebook_data)
#        django_user_data_valid = {'last_name': 'Oleary', 'image': 'http://graph.facebook.com/me/picture?type=large', 'about_me': None, 'timezone':-5, 'id': '1225707780', 'first_name': 'Shane', 'verified': True, 'facebook_name': 'Shane Oleary', 'location': {'id': None, 'name': None}, 'facebook_id': '1225707780', 'image_thumb': 'http://graph.facebook.com/me/picture', 'website_url': None, 'username': u'shane_oleary', 'date_of_birth': None, 'birthday': '04/07', 'link': 'http://www.facebook.com/profile.php?id=1225707780', 'name': 'Shane Oleary', 'gender': 'man', 'updated_time': '2010-04-01T14:26:55+0000', 'facebook_profile_url': 'http://www.facebook.com/profile.php?id=1225707780'}
#        self.assertEqualUserData(django_user_data, django_user_data_valid)
#
#    def assertEqualUserData(self, a, b):
#        def normalize(user_data_dict):
#            user_data_dict.pop('password1', False)
#            user_data_dict.pop('password2', False)
#            return user_data_dict
#        a_normal = normalize(a)
#        b_normal = normalize(b)
#        unequal = []
#        for field, value in a_normal.items():
#            if value != b_normal.get(field):
#                unequal.append((field, value, b_normal.get(field)))
#        if unequal:
#            raise ValueError('Unequal for %s dict %s should have been %s' % (unequal, a_normal, b_normal))





if __name__ == '__main__':
    
    unittest.main()

from __future__ import with_statement
from django_facebook import exceptions as facebook_exceptions
from django_facebook.api import get_facebook_graph
from django_facebook.connect import connect_user, CONNECT_ACTIONS
from django_facebook.official_sdk import GraphAPIError
from django_facebook.tests.base import FacebookTest
import logging
import unittest
from django.contrib.auth import models as auth_models

logger = logging.getLogger(__name__)

    
    
class UserConnectTest(FacebookTest):
    '''
    Tests the connect user functionality
    
    TODO
    - Test for short usernames and fall back to names
    - Retry on facebook connection errors
    - Taken username errors
    - Next param op mystyle
    '''
    fixtures = ['users.json']
    
    def test_invalid_token(self):
        self.assertRaises(AssertionError, connect_user, self.request, access_token='invalid')

    def test_no_email_registration(self):
        self.assertRaises(facebook_exceptions.IncompleteProfileError, connect_user, self.request, access_token='no_email')
    
    def test_current_user(self):
        facebook = get_facebook_graph(access_token='tschellenbach', persistent_token=False)
        action, user = connect_user(self.request, facebook_graph=facebook)
        assert action == CONNECT_ACTIONS.LOGIN
    
    def test_new_user(self):
        facebook = get_facebook_graph(access_token='new_user', persistent_token=False)
        action, user = connect_user(self.request, facebook_graph=facebook)
    
    
    
    
class FQLTest(FacebookTest):
    def test_base_fql(self):
        facebook = get_facebook_graph(access_token='tschellenbach', persistent_token=False)
        query = 'SELECT name FROM user WHERE uid = me()'
        self.assertRaises(GraphAPIError, facebook.fql, query);
    
    
    
    
    
class DataTransformTest(FacebookTest):
    def test_doctest_api(self):
        from django_facebook import api
        import doctest
        doctest.testmod(api)





if __name__ == '__main__':
    
    unittest.main()

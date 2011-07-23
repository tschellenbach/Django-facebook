'''
Alpha/Testing code....

A generic Facebook API

- Which actually is supported and updated
- Tested so people can contribute smoothly
- Exceptions
- Logging for debugging
'''
import os
from django.http import QueryDict
os.environ['DJANGO_SETTINGS_MODULE'] = 'facebook_example.settings'
from django_facebook import settings as facebook_settings
import logging
import urllib
import urllib2
logger = logging.getLogger(__name__)



class OpenFacebookException(Exception):
    pass

class OAuthException(OpenFacebookException):
    pass


print 'hello world'
def test_facebook():
    token = FacebookAuthorization.get_app_access_token()
    #print FacebookAuthorization.create_test_user(token)
    token = '215464901804004|2.AQBHGHuWRllFbN4E.3600.1311465600.0-100002619711402|EtaLBkqHGsTa0cpMlFA4bmL4aAc'
    token = '215464901804004|2.AQAwYr7AYNkKS9Rn.3600.1311469200.0-100002646981608|NtiF-ioL-98NF5juQtN2UXc0wKU'
    facebook = OpenFacebook(token)
    print facebook.me()
    
    print facebook.get('cocacola')
    
    print facebook.post_on_wall('me', 'the writing is one the wall')
    #print facebook.get('me/permissions')
    print facebook.get('me/feed')
    #this should give a lazy iterable instead of the default result..
    
    #print facebook.get_many('cocacola', 'me')
    


class FacebookAuthorization(object):
    @classmethod
    def get_app_access_token(cls):
        '''
        Get the access_token for the app that can be used for insights and creating test users
        application_id = retrieved from the developer page
        application_secret = retrieved from the developer page
        returns the application access_token
        '''
        # Get an app access token
        args = {'grant_type':'client_credentials',
                'client_id':facebook_settings.FACEBOOK_APP_ID,
                'client_secret':facebook_settings.FACEBOOK_APP_SECRET}
        
        response = OpenFacebook._request('https://graph.facebook.com/oauth/access_token?' + 
                                  urllib.urlencode(args))
        print response
        return response['access_token']
    
    @classmethod
    def create_test_user(cls, access_token):
        '''
        My test user
        {u'access_token': u'215464901804004|2.AQBHGHuWRllFbN4E.3600.1311465600.0-100002619711402|EtaLBkqHGsTa0cpMlFA4bmL4aAc', u'password': u'564490991', u'login_url': u'https://www.facebook.com/platform/test_account_login.php?user_id=100002619711402&n=3c5fAe1nNVk0HaJ', u'id': u'100002619711402', u'email': u'hello_luncrwh_world@tfbnw.net'}
        #with write permissions
        {u'access_token': u'215464901804004|2.AQAwYr7AYNkKS9Rn.3600.1311469200.0-100002646981608|NtiF-ioL-98NF5juQtN2UXc0wKU', u'password': u'1291131687', u'login_url': u'https://www.facebook.com/platform/test_account_login.php?user_id=100002646981608&n=yU5ZvTTv4UjJJOt', u'id': u'100002646981608', u'email': u'hello_klsdgrf_world@tfbnw.net'}
        '''
        args = {
            'access_token':access_token,
            'installed': True,
            'name': 'Hello World',
            'method': 'post',
            'permissions': 'read_stream,publish_stream',
        }
        
        response = OpenFacebook._request(
                'https://graph.facebook.com/%s/accounts/test-users?' % facebook_settings.FACEBOOK_APP_ID + 
                                  urllib.urlencode(args))
        
        return response
                  



class OpenFacebook(object):
    '''
    Response parsing is weird, sometimes json, sometimes plain string...
    '''
    def __init__(self, access_token=None):
        self.access_token = access_token
        self.api_url = 'https://graph.facebook.com/'
        
    def get(self, path, **kwargs):
        return self.request(path, **kwargs)
    
    def get_many(self, *ids, **kwargs):
        kwargs['ids'] = ','.join(ids)
        return self.request(**kwargs)
    
    def set(self, path, **post_data):
        assert self.access_token, 'Write operations require an access token'
        self.request(path, post_data=post_data)
    
    def post_on_wall(self, path, message, attachment=None):
        """Writes a wall post to the given profile's wall.

        We default to writing to the authenticated user's wall if no
        profile_id is specified.

        attachment adds a structured attachment to the status message being
        posted to the Wall. It should be a dictionary of the form:

            {"name": "Link name"
             "link": "http://www.example.com/",
             "caption": "{*actor*} posted a new review",
             "description": "This is a longer description of the attachment",
             "picture": "http://www.example.com/thumbnail.jpg"}
        """
        if not attachment:
            attachment = {}
        wall_path = '%s/feed/' % path
        return self.set(wall_path, message=message, **attachment)
    
    def delete(self, *args, **kwargs):
        kwargs['method'] = 'delete'
        self.request(*args, **kwargs)
        
    def me(self):
        return self.get('me')
        
    def create_test_user(self, installed=True, name='test_user', permissions='read_stream', method='post', access_token='app token'):
        pass
        
    def request(self, path='', post_data=None, **params):
        '''
        Main function for sending the request to facebook
        '''
        print path
        if self.access_token:
            params['access_token'] = self.access_token
        url = '%s%s?%s' % (self.api_url, path, urllib.urlencode(params))
        print path
        response = self._request(url, post_data)
        return response
    
    @classmethod
    def _request(cls, url, post_data=None, timeout=5, attempts=2):
        '''
        request the given url and parse it as json
        
        urllib2 raises errors on different status codes so use a try except
        '''
        logger.info('requesting url %s with post data %s', url, post_data)
        from django.utils import simplejson
        print url
        import urllib2
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Open Facebook Python')]
        #give it a few shots, connection is buggy at times
        
        while attempts:
            print '.', attempts
            response_file = None
            post_string = urllib.urlencode(post_data) if post_data else None
            try:
                try:
                    response_file = opener.open(url, post_string, timeout=timeout)
                except (urllib2.HTTPError,), e:
                    #catch the silly status code errors
                    if 'HTTP Error' in unicode(e):
                        response_file = e
                    else:
                        raise
                response = response_file.read().decode('utf8')
                break
            except (urllib2.HTTPError, urllib2.URLError), e:
                attempts -= 1
                if not attempts:
                    raise
            finally:
                if response_file:
                    response_file.close()        
        
        from simplejson.decoder import JSONDecodeError
        try:
            parsed_response = simplejson.loads(response)
            if getattr(response, 'error', False):
                cls.raise_error(response['error']['type'], response['error']['message'])
                                     
        except JSONDecodeError, e:
            parsed_response = QueryDict(response, True)
        
            
        return parsed_response
    
    @classmethod
    def raise_error(self, type, message):
        '''
        Search for a corresponding error class and fall back to open facebook exception
        '''
        error_class = globals().get(type)
        if not issubclass(error_class, OpenFacebookException):
            error_class = None
            
        if not error_class:
            error_class = OpenFacebookException
        
        raise error_class(message)
        
            
    
    

    

if __name__ == '__main__':
    test_facebook()

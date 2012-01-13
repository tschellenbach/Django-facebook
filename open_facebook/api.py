# -*- coding: utf-8 -*-
'''
=============================================
Open Facebook - A generic Facebook API
=============================================

This API is actively maintained, just fork on github if you wan
to improve things.
Follow the author: Thierry Schellenbach (@tschellenbach)
blog: http://www.mellowmorning.com/
my company: http://www.fashiolista.com/

Features:
- <em>Supported and maintained</em>
- Tested so people can contribute smoothly
- Facebook exceptions are mapped
- Logging

TODO
- django querydict replacement (urlencode breaks on utf8)

Syntax
>>> facebook.get('me')
>>> facebook.set('1789/comments', message='check out fashiolista')
>>> facebook.set('me/feed', message='check out fashiolista', url='http://www.fashiolista.com')
>>> facebook.set('cocacola/likes')

Maybe when the facebook api get's more stable we will move to a chaining syntax
Which validates input
facebook('me').loves()
facebook('myalbum').comment('Fashiolista is awesome ♥')
Currently that would be a bad idea though because of maintenance

'''
from django.http import QueryDict
from django_facebook import settings as facebook_settings
from open_facebook import exceptions as facebook_exceptions
from open_facebook.utils import json, encode_params, send_warning
import logging
import urllib
import urllib2
from django_facebook.utils import to_int
logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 8
REQUEST_ATTEMPTS = 2


try:
    import django_statsd
except ImportError:
    django_statsd = None


class FacebookConnection(object):
    '''
    Shared class for sending requests to facebook and parsing
    the api response
    '''
    api_url = 'https://graph.facebook.com/'
    # this older url is still used for fql requests
    old_api_url = 'https://api.facebook.com/method/'

    @classmethod
    def request(cls, path='', post_data=None, old_api=False, **params):
        '''
        Main function for sending the request to facebook
        '''
        api_base_url = cls.old_api_url if old_api else cls.api_url
        if getattr(cls, 'access_token', None):
            params['access_token'] = cls.access_token
        url = '%s%s?%s' % (api_base_url, path, urllib.urlencode(params))
        response = cls._request(url, post_data)
        return response

    @classmethod
    def _request(cls, url, post_data=None, timeout=REQUEST_TIMEOUT,
                 attempts=REQUEST_ATTEMPTS):
        '''
        request the given url and parse it as json
        urllib2 raises errors on different status codes so use a try except
        '''
        logger.info('requesting url %s with post data %s', url, post_data)
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Open Facebook Python')]
        # give it a few shots, connection is buggy at times

        path = url.split('?', 1)[0].rsplit('/', 1)[-1].replace('.', '_')
        while attempts:
            response_file = None
            encoded_params = encode_params(post_data) if post_data else None
            post_string = (urllib.urlencode(encoded_params)
                           if post_data else None)
            try:
                if django_statsd:
                    django_statsd.start('facebook.%s' % path)

                try:
                    # For older python versions you could leave out the timeout
                    # response_file = opener.open(url, post_string)
                    response_file = opener.open(url, post_string,
                                                timeout=timeout)
                except (urllib2.HTTPError,), e:
                    # catch the silly status code errors
                    if 'http error' in str(e).lower():
                        response_file = e
                    else:
                        raise
                response = response_file.read().decode('utf8')
                break
            except (urllib2.HTTPError, urllib2.URLError), e:
                logger.warn('facebook encountered a timeout or error %s',
                            unicode(e))
                attempts -= 1
                if not attempts:
                    raise
            finally:
                if response_file:
                    response_file.close()
                if django_statsd:
                    django_statsd.stop('facebook.%s' % path)

        try:
            parsed_response = json.loads(response)
            logger.info('facebook send response %s' % parsed_response)
        except Exception, e:
            # using exception because we need to support multiple json libs :S
            parsed_response = QueryDict(response, True)
            logger.info('facebook send response %s' % parsed_response)

        if parsed_response and isinstance(parsed_response, dict):
            # of course we have two different syntaxes
            if parsed_response.get('error'):
                cls.raise_error(parsed_response['error']['type'],
                                parsed_response['error']['message'])
            elif parsed_response.get('error_code'):
                cls.raise_error(parsed_response['error_code'],
                                parsed_response['error_msg'])

        return parsed_response

    @classmethod
    def raise_error(self, error_type, message):
        '''
        Search for a corresponding error class and fall back to
        open facebook exception
        '''
        import re
        error_class = None
        if not isinstance(error_type, int):
            error_class = getattr(facebook_exceptions, error_type, None)
        if error_class and not issubclass(error_class,
                                          facebook_exceptions.OpenFacebookException):
            error_class = None
        # map error classes to facebook error ids
        # define a string to match a single error,
        # use ranges for complexer cases
        # also see http://fbdevwiki.com/wiki/Error_codes#User_Permission_Errors
        classes = [getattr(facebook_exceptions, e, None)
                   for e in dir(facebook_exceptions)]
        exception_classes = [e for e in classes if getattr(
            e, 'codes', None) and issubclass(
                e, facebook_exceptions.OpenFacebookException)]
        exception_classes.sort(key=lambda e: e.range())

        # find the error code
        error_code = None
        error_code_re = re.compile('\(#(\d+)\)')
        matches = error_code_re.match(message)
        matching_groups = matches.groups() if matches else None
        if matching_groups:
            error_code = to_int(matching_groups[0]) or None

        for class_ in exception_classes:
            codes_list = class_.codes_list()
            # match the error class
            matching_error_class = None
            for code in codes_list:
                if isinstance(code, basestring):
                    # match on string
                    key = code
                    if key in message:
                        matching_error_class = class_
                        break
                elif isinstance(code, tuple):
                    start, stop = code
                    if error_code and start <= error_code <= stop:
                        matching_error_class = class_
                        break
                elif isinstance(code, (int, long)):
                    if int(code) == error_code:
                        matching_error_class = class_
                        break
                else:
                    raise(
                        ValueError, 'Dont know how to handle %s of ' \
                        'type %s' % (code, type(code)))
            #tell about the happy news if we found something
            if matching_error_class:
                error_class = matching_error_class
                break

        if 'Missing' in message and 'parameter' in message:
            error_class = facebook_exceptions.MissingParameter

        if not error_class:
            error_class = facebook_exceptions.OpenFacebookException

        raise error_class(message)


class FacebookAuthorization(FacebookConnection):
    '''
    Methods for getting us an access token
    There are several flows we must support
    - js authentication flow (signed cookie)
    - facebook app authentication flow (signed cookie)
    - facebook oauth redirect (code param in url)
    These 3 options need to be converted to an access token

    Also handles several testing scenarios
    - get app access token
    - create test user
    - get_or_create_test_user
    '''
    @classmethod
    def convert_code(cls, code,
        redirect_uri='http://local.mellowmorning.com:8000/facebook/connect/'):
        '''
        Turns a code into an access token
        '''
        kwargs = dict(client_id=facebook_settings.FACEBOOK_APP_ID)
        kwargs['client_secret'] = facebook_settings.FACEBOOK_APP_SECRET
        kwargs['code'] = code
        kwargs['redirect_uri'] = redirect_uri
        response = cls.request('oauth/access_token', **kwargs)
        return response

    @classmethod
    def parse_signed_data(cls, signed_request,
                          secret=facebook_settings.FACEBOOK_APP_SECRET):
        '''
        Thanks to
        http://stackoverflow.com/questions/3302946/how-to-base64-url-decode-in-python
        and
        http://sunilarora.org/parsing-signedrequest-parameter-in-python-bas
        '''
        from open_facebook.utils import base64_url_decode_php_style
        l = signed_request.split('.', 2)
        encoded_sig = l[0]
        payload = l[1]
        from open_facebook.utils import json
        sig = base64_url_decode_php_style(encoded_sig)
        import hmac
        import hashlib
        data = json.loads(base64_url_decode_php_style(payload))

        algo = data.get('algorithm').upper()
        if  algo != 'HMAC-SHA256':
            send_warning('Unknown algorithm we only support HMAC-SHA256 ' \
                         'user asked for %s', algo)
            logger.error('Unknown algorithm')
            return None
        else:
            expected_sig = hmac.new(secret, msg=payload,
                                    digestmod=hashlib.sha256).digest()

        if sig != expected_sig:
            send_warning('Signature %s didnt match the expected ' \
                         'signature %s', sig, expected_sig)
            return None
        else:
            logger.debug('valid signed request received..')
            return data

    @classmethod
    def get_app_access_token(cls):
        '''
        Get the access_token for the app that can be used for
        insights and creating test users
        application_id = retrieved from the developer page
        application_secret = retrieved from the developer page
        returns the application access_token
        '''
        kwargs = {
            'grant_type': 'client_credentials',
            'client_id': facebook_settings.FACEBOOK_APP_ID,
            'client_secret': facebook_settings.FACEBOOK_APP_SECRET,
        }
        response = cls.request('oauth/access_token', **kwargs)
        return response['access_token']

    @classmethod
    def create_test_user(cls, app_access_token, permissions=None):
        '''
        My test user
        {u'access_token': u'215464901804004|2.AQBHGHuWRllFbN4E.3600.1311465600.0-100002619711402|EtaLBkqHGsTa0cpMlFA4bmL4aAc', u'password': u'564490991', u'login_url': u'https://www.facebook.com/platform/test_account_login.php?user_id=100002619711402&n=3c5fAe1nNVk0HaJ', u'id': u'100002619711402', u'email': u'hello_luncrwh_world@tfbnw.net'}
        #with write permissions
        {u'access_token': u'215464901804004|2.AQAwYr7AYNkKS9Rn.3600.1311469200.0-100002646981608|NtiF-ioL-98NF5juQtN2UXc0wKU', u'password': u'1291131687', u'login_url': u'https://www.facebook.com/platform/test_account_login.php?user_id=100002646981608&n=yU5ZvTTv4UjJJOt', u'id': u'100002646981608', u'email': u'hello_klsdgrf_world@tfbnw.net'}
        offline permissions
        {u'access_token': u'215464901804004|b8d73771906a072829857c2f.0-100002661892257|DALPDLEZl4B0BNm0RYXnAsuri-I', u'password': u'1932271520', u'login_url': u'https://www.facebook.com/platform/test_account_login.php?user_id=100002661892257&n=Zdu5jdD4tjNsfma', u'id': u'100002661892257', u'email': u'hello_nrthuig_world@tfbnw.net'}
        '''
        if not permissions:
            permissions = 'read_stream,publish_stream,' \
                          'user_photos,offline_access'

        kwargs = {
            'access_token': app_access_token,
            'installed': True,
            'name': 'Hello World',
            'method': 'post',
            'permissions': permissions,
        }
        path = '%s/accounts/test-users' % facebook_settings.FACEBOOK_APP_ID
        response = cls.request(path, **kwargs)

        return response

    @classmethod
    def get_or_create_test_user(cls, app_access_token, permissions=None):
        if not permissions:
            permissions = ['read_stream', 'publish_stream',
                           'user_photos', 'offline_access']

        kwargs = {
            'access_token': app_access_token,
        }
        path = '%s/accounts/test-users' % facebook_settings.FACEBOOK_APP_ID

        response = cls.request(path, **kwargs)

        return response


class OpenFacebook(FacebookConnection):
    '''
    ========================================
    Getting your authentication started
    ========================================
    OpenFacebook gives you access to the facebook api.
    For most user related actions you need an access_token.
    There are 3 ways of getting a facebook access_token
    1.) code is passed as request parameter and traded for an
        access_token using the api
    2.) code is passed through a signed cookie and traded for an access_token
    3.) access_token is passed directly (retrieved through javascript, which
        would be bad security, or through one of the mobile flows.)
    Requesting a code for flow 1 and 2 is quite easy. Facebook doc's are here:
    http://developers.facebook.com/docs/authentication/
    Client side code request
    For the client side flow simply use the FB.login functionality
    and on the landing page call
    facebook = get_facebook_graph(request)
    print facebook.me()

    Server side code request

    facebook = get_facebook_graph(request)
    print facebook.me()

    ========================================
    Actually using the facebook API
    ========================================
    After retrieving an access token API calls are relatively straigh forward

    Getting info about me
    facebook.get('me')

    Learning some more about fashiolista
    facebook.get('fashiolista')

    Writing your first comment
    facebook.set('fashiolista/comments', message='I love Fashiolista!')

    Posting to a users wall
    facebook.set('me/feed', message='check out fashiolista',
                 url='http://www.fashiolista.com')

    Liking a page
    facebook.set('fashiolista/likes')

    Executing some fql
    facebook.fql('SELECT name FROM user WHERE uid = me()')

    Uploading pictures
    photo_urls = [
        'http://e.fashiocdn.com/images/entities/0/7/B/I/9/0.365x365.jpg',
        'http://e.fashiocdn.com/images/entities/0/5/e/e/r/0.365x365.jpg',
    ]
    for photo in photo_urls:
        print facebook.set('me/feed', message='Check out Fashiolista',
                           picture=photo, url='http://www.fashiolista.com')

    ========================================
    Contributing
    ========================================

    This API is actively maintained, just fork on github if you want to
    improve things.
    Follow the author: Thierry Schellenbach (@tschellenbach)
    blog: http://www.mellowmorning.com/
    my company: http://www.fashiolista.com/

    '''
    def __init__(self, access_token=None, prefetched_data=None,
                 expires=None, current_user_id=None):
        self.access_token = access_token
        # extra data coming from signed cookies
        self.prefetched_data = prefetched_data

        # store to enable detection for offline usage
        self.expires = expires

        # hook to store the current user id if representing the
        # facebook connection to a logged in user :)
        self.current_user_id = current_user_id

    def is_authenticated(self):
        '''
        Ask facebook if we have access to the users data
        '''
        try:
            me = self.me()
        except facebook_exceptions.OpenFacebookException:
            me = None
        authenticated = bool(me)
        return authenticated

    def get(self, path, **kwargs):
        response = self.request(path, **kwargs)
        return response

    def get_many(self, *ids, **kwargs):
        kwargs['ids'] = ','.join(ids)
        return self.request(**kwargs)

    def set(self, path, params=None, **post_data):
        assert self.access_token, 'Write operations require an access token'
        if not params:
            params = {}
        params['method'] = 'post'

        response = self.request(path, post_data=post_data, **params)
        return response

    def delete(self, *args, **kwargs):
        kwargs['method'] = 'delete'
        self.request(*args, **kwargs)

    def fql(self, query, **kwargs):
        """Runs the specified query against the Facebook FQL API.
        """
        kwargs['format'] = 'JSON'
        kwargs['query'] = query
        path = 'fql.query'

        response = self.request(path, old_api=True, **kwargs)

        return response

    def me(self):
        '''
        Cached method of requesting information about me
        '''
        me = getattr(self, '_me', None)
        if me is None:
            self._me = me = self.get('me')

        return me

    def my_image_url(self, size=None):
        '''
        Returns the image url from your profile
        '''
        query_dict = QueryDict('', True)
        if size:
            query_dict['type'] = size
        query_dict['access_token'] = self.access_token

        url = '%sme/picture?%s' % (self.api_url, query_dict.urlencode())
        return url

    def request(self, path='', post_data=None, old_api=False, **params):
        '''
        Main function for sending the request to facebook
        '''
        api_base_url = self.old_api_url if old_api else self.api_url
        if getattr(self, 'access_token', None):
            params['access_token'] = self.access_token
        url = '%s%s?%s' % (api_base_url, path, urllib.urlencode(params))
        logger.info('requesting url %s', url)
        response = self._request(url, post_data)
        return response

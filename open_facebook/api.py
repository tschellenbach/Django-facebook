# -*- coding: utf-8 -*-
'''

Open Facebook - Pythonic access to the open graph
=================================================

Open Facebook allows you to use Facebook's open graph API with simple python code

**Features**:

* Supported and maintained
* Tested so people can contribute
* Facebook exceptions are mapped
* Logging


**Basic examples**::

    facebook = OpenFacebook(access_token)

    # Getting info about me
    facebook.get('me')

    # Learning some more about fashiolista
    facebook.get('fashiolista')

    # Writing your first comment
    facebook.set('fashiolista/comments', message='I love Fashiolista!')


    # Posting to a users wall
    facebook.set('me/feed', message='check out fashiolista',
                 url='http://www.fashiolista.com')

    # Liking a page
    facebook.set('fashiolista/likes')

    # Getting who likes cocacola
    facebook.set('cocacola/likes')

    # Use fql to retrieve your name
    facebook.fql('SELECT name FROM user WHERE uid = me()')

    # Executing fql in batch
    facebook.batch_fql([
        'SELECT uid, name, pic_square FROM user WHERE uid = me()',
        'SELECT uid, rsvp_status FROM event_member WHERE eid=12345678',
    ])

    # Uploading pictures
    photo_urls = [
        'http://e.fashiocdn.com/images/entities/0/7/B/I/9/0.365x365.jpg',
        'http://e.fashiocdn.com/images/entities/0/5/e/e/r/0.365x365.jpg',
    ]
    for photo in photo_urls:
        print facebook.set('me/feed', message='Check out Fashiolista',
                           picture=photo, url='http://www.fashiolista.com')


**Getting an access token**

Once you get your access token, Open Facebook gives you access to the Facebook API
There are 3 ways of getting a facebook access_token and these are currently
implemented by Django Facebook.

1. code is passed as request parameter and traded for an
    access_token using the api

2. code is passed through a signed cookie and traded for an access_token

3. access_token is passed directly (retrieved through javascript, which
    would be bad security, or through one of the mobile flows.)

If you are looking to develop your own flow for a different framework have a look at
Facebook's documentation:
http://developers.facebook.com/docs/authentication/

Also have a look at the :class:`.FacebookRequired` decorator and :func:`get_persistent_graph` function to
understand the required functionality


**Api docs**:


'''
from django.http import QueryDict
from django_facebook import settings as facebook_settings
from open_facebook import exceptions as facebook_exceptions
from open_facebook.utils import json, encode_params, send_warning, memoized, \
    stop_statsd, start_statsd
import logging
import urllib
import urllib2
from django_facebook.utils import to_int
import ssl
import re
from urlparse import urlparse
logger = logging.getLogger(__name__)


# base timeout, actual timeout will increase when requests fail
REQUEST_TIMEOUT = 10
# two retries was too little, sometimes facebook is a bit flaky
REQUEST_ATTEMPTS = 3


class FacebookConnection(object):

    '''
    Shared utility class implementing the parsing
    of Facebook API responses
    '''
    api_url = 'https://graph.facebook.com/'
    # this older url is still used for fql requests
    old_api_url = 'https://api.facebook.com/method/'

    @classmethod
    def request(cls, path='', post_data=None, old_api=False, **params):
        '''
        Main function for sending the request to facebook

        **Example**::
            FacebookConnection.request('me')

        :param path:
            The path to request, examples: /me/friends/, /me/likes/

        :param post_data:
            A dictionary of data to post

        :param parms:
            The get params to include
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
        # change fb__explicitly_shared to fb:explicitly_shared
        if post_data:
            post_data = dict(
                (k.replace('__', ':'), v) for k, v in post_data.items())

        logger.info('requesting url %s with post data %s', url, post_data)
        post_request = (post_data is not None or 'method=post' in url)

        if post_request and facebook_settings.FACEBOOK_READ_ONLY:
            logger.info('running in readonly mode')
            response = dict(id=123456789, setting_read_only=True)
            return response

        # nicely identify ourselves before sending the request
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Open Facebook Python')]

        # get the statsd path to track response times with
        path = urlparse(url).path
        statsd_path = path.replace('.', '_')

        # give it a few shots, connection is buggy at times
        timeout_mp = 0
        while attempts:
            # gradually increase the timeout upon failure
            timeout_mp += 1
            extended_timeout = timeout * timeout_mp
            response_file = None
            encoded_params = encode_params(post_data) if post_data else None
            post_string = (urllib.urlencode(encoded_params)
                           if post_data else None)
            try:
                start_statsd('facebook.%s' % statsd_path)

                try:
                    response_file = opener.open(
                        url, post_string, timeout=extended_timeout)
                    response = response_file.read().decode('utf8')
                except (urllib2.HTTPError,), e:
                    response_file = e
                    response = response_file.read().decode('utf8')
                    # Facebook sents error codes for many of their flows
                    # we still want the json to allow for proper handling
                    msg_format = 'FB request, error type %s, code %s'
                    logger.warn(msg_format, type(e), getattr(e, 'code', None))
                    # detect if its a server or application error
                    server_error = cls.is_server_error(e, response)
                    if server_error:
                        # trigger a retry
                        raise urllib2.URLError(
                            'Facebook is down %s' % response)
                break
            except (urllib2.HTTPError, urllib2.URLError, ssl.SSLError), e:
                # These are often temporary errors, so we will retry before
                # failing
                error_format = 'Facebook encountered a timeout (%ss) or error %s'
                logger.warn(error_format, extended_timeout, unicode(e))
                attempts -= 1
                if not attempts:
                    # if we have no more attempts actually raise the error
                    error_instance = facebook_exceptions.convert_unreachable_exception(
                        e)
                    error_msg = 'Facebook request failed after several retries, raising error %s'
                    logger.warn(error_msg, error_instance)
                    raise error_instance
            finally:
                if response_file:
                    response_file.close()
                stop_statsd('facebook.%s' % statsd_path)

        # Faceboook response is either
        # Valid json
        # A string which is a querydict (a=b&c=d...etc)
        # A html page stating FB is having trouble (but that shouldnt reach
        # this part of the code)
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
                                parsed_response['error']['message'],
                                parsed_response['error'].get('code'))
            elif parsed_response.get('error_code'):
                cls.raise_error(parsed_response['error_code'],
                                parsed_response['error_msg'])

        return parsed_response

    @classmethod
    def is_server_error(cls, e, response):
        '''
        Checks an HTTPError to see if Facebook is down or we are using the
        API in the wrong way
        Facebook doesn't clearly distinquish between the two, so this is a bit
        of a hack
        '''
        from open_facebook.utils import is_json
        server_error = False
        if hasattr(e, 'code') and e.code == 500:
            server_error = True

        # Facebook status codes are used for application logic
        # http://fbdevwiki.com/wiki/Error_codes#User_Permission_Errors
        # The only way I know to detect an actual server error is to check if
        # it looks like their error page
        # TODO: think of a better solution....
        error_matchers = [
            '<title>Facebook | Error</title>',
            'Sorry, something went wrong.'
        ]
        is_error_page = all(
            [matcher in response for matcher in error_matchers])
        if is_error_page:
            server_error = True

        # if it looks like json, facebook is probably not down
        if is_json(response):
            server_error = False

        return server_error

    @classmethod
    def raise_error(cls, error_type, message, error_code=None):
        '''
        Lookup the best error class for the error and raise it

        **Example**::

            FacebookConnection.raise_error(10, 'OAuthException')

        :param error_type:
            the error type from the facebook api call

        :param message:
            the error message from the facebook api call

        :param error_code:
            optionally the error code which facebook send
        '''
        default_error_class = facebook_exceptions.OpenFacebookException

        # get the error code
        error_code = error_code or cls.get_code_from_message(message)
        # also see http://fbdevwiki.com/wiki/Error_codes#User_Permission_Errors
        logger.info('Trying to match error code %s to error class', error_code)

        # lookup by error code takes precedence
        error_class = cls.match_error_code(error_code)

        # try to get error class by direct lookup
        if not error_class:
            if not isinstance(error_type, int):
                error_class = getattr(facebook_exceptions, error_type, None)
            if error_class and not issubclass(error_class, default_error_class):
                error_class = None

        # hack for missing parameters
        if 'Missing' in message and 'parameter' in message:
            error_class = facebook_exceptions.MissingParameter

        # hack for Unsupported delete request
        if 'Unsupported delete request' in message:
            error_class = facebook_exceptions.UnsupportedDeleteRequest

        # fallback to the default
        if not error_class:
            error_class = default_error_class

        logger.info('Matched error to class %s', error_class)
        error_message = message
        if error_code:
            # this is handy when adding new exceptions for facebook errors
            error_message = u'%s (error code %s)' % (message, error_code)

        raise error_class(error_message)

    @classmethod
    def get_code_from_message(cls, message):
        # map error classes to facebook error codes
        # find the error code
        error_code = None
        error_code_re = re.compile('\(#(\d+)\)')
        matches = error_code_re.match(message)
        matching_groups = matches.groups() if matches else None
        if matching_groups:
            error_code = to_int(matching_groups[0]) or None

        return error_code

    @classmethod
    def get_sorted_exceptions(cls):
        from open_facebook.exceptions import get_exception_classes
        exception_classes = get_exception_classes()
        exception_classes.sort(key=lambda e: e.range())
        return exception_classes

    @classmethod
    def match_error_code(cls, error_code):
        '''
        Return the right exception class for the error code
        '''
        exception_classes = cls.get_sorted_exceptions()
        error_class = None
        for class_ in exception_classes:
            codes_list = class_.codes_list()
            # match the error class
            matching_error_class = None
            for code in codes_list:
                if isinstance(code, tuple):
                    start, stop = code
                    if error_code and start <= error_code <= stop:
                        matching_error_class = class_
                        logger.info('Matched error on code %s', code)
                elif isinstance(code, (int, long)):
                    if int(code) == error_code:
                        matching_error_class = class_
                        logger.info('Matched error on code %s', code)
                else:
                    raise(
                        ValueError, 'Dont know how to handle %s of '
                        'type %s' % (code, type(code)))
            # tell about the happy news if we found something
            if matching_error_class:
                error_class = matching_error_class
                break
        return error_class


class FacebookAuthorization(FacebookConnection):

    '''
    Methods for getting us an access token

    There are several flows we must support
    * js authentication flow (signed cookie)
    * facebook app authentication flow (signed cookie)
    * facebook oauth redirect (code param in url)
    These 3 options need to be converted to an access token

    Also handles several testing scenarios
    * get app access token
    * create test user
    * get_or_create_test_user
    '''
    @classmethod
    def convert_code(cls, code,
                     redirect_uri='http://local.mellowmorning.com:8000/facebook/connect/'):
        '''
        Turns a code into an access token

        **Example**::

            FacebookAuthorization.convert_code(code)

        :param code:
            The code to convert

        :param redirect_uri:
            The redirect uri with which the code was requested

        :returns: dict

        '''
        kwargs = cls._client_info()
        kwargs['code'] = code
        kwargs['redirect_uri'] = redirect_uri
        response = cls.request('oauth/access_token', **kwargs)
        return response

    @classmethod
    def extend_access_token(cls, access_token):
        '''
        https://developers.facebook.com/roadmap/offline-access-removal/
        We can extend the token only once per day
        Normal short lived tokens last 1-2 hours
        Long lived tokens (given by extending) last 60 days

        **Example**::

            FacebookAuthorization.extend_access_token(access_token)

        :param access_token:
            The access_token to extend

        :returns: dict
        '''
        kwargs = cls._client_info()
        kwargs['grant_type'] = 'fb_exchange_token'
        kwargs['fb_exchange_token'] = access_token
        response = cls.request('oauth/access_token', **kwargs)
        return response

    @classmethod
    def _client_info(cls):
        kwargs = dict(client_id=facebook_settings.FACEBOOK_APP_ID)
        kwargs['client_secret'] = facebook_settings.FACEBOOK_APP_SECRET
        return kwargs

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
        if algo != 'HMAC-SHA256':
            error_format = 'Unknown algorithm we only support HMAC-SHA256 user asked for %s'
            error_message = error_format % algo
            send_warning(error_message)
            logger.error('Unknown algorithm')
            return None
        else:
            expected_sig = hmac.new(secret, msg=payload,
                                    digestmod=hashlib.sha256).digest()

        if sig != expected_sig:
            error_format = 'Signature %s didnt match the expected signature %s'
            error_message = error_format % (sig, expected_sig)
            send_warning(error_message)
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
    @memoized
    def get_cached_app_access_token(cls):
        '''
        Caches the access token in memory, good for speeding up testing
        '''
        app_access_token = cls.get_app_access_token()
        return app_access_token

    @classmethod
    def create_test_user(cls, app_access_token, permissions=None, name=None):
        '''
        Creates a test user with the given permissions and name

        :param app_access_token:
            The application's access token

        :param permissions:
            The list of permissions to request for the test user

        :param name:
            Optionally specify the name
        '''
        if not permissions:
            permissions = ['read_stream', 'publish_stream',
                           'user_photos,offline_access']
        if isinstance(permissions, list):
            permissions = ','.join(permissions)

        default_name = 'Permissions %s' % permissions.replace(
            ',', ' ').replace('_', '')
        name = name or default_name

        kwargs = {
            'access_token': app_access_token,
            'installed': True,
            'name': name,
            'method': 'post',
            'permissions': permissions,
        }
        path = '%s/accounts/test-users' % facebook_settings.FACEBOOK_APP_ID
        # add the test user data to the test user data class
        test_user_data = cls.request(path, **kwargs)
        test_user_data['name'] = name
        test_user = TestUser(test_user_data)

        return test_user

    @classmethod
    def get_or_create_test_user(cls, app_access_token, name=None, permissions=None, force_create=False):
        '''
        There is no supported way of get or creating a test user
        However
        - creating a test user takes around 5s
        - you an only create 500 test users
        So this slows your testing flow quite a bit.

        This method checks your test users
        Queries their names (stores the permissions in the name)

        '''
        if not permissions:
            permissions = ['read_stream', 'publish_stream', 'publish_actions',
                           'user_photos,offline_access']
        if isinstance(permissions, list):
            permissions = ','.join(permissions)

        # hacking the permissions into the name of the test user
        default_name = 'Permissions %s' % permissions.replace(
            ',', ' ').replace('_', '')
        name = name or default_name

        # retrieve all test users
        test_users = cls.get_test_users(app_access_token)
        user_id_dict = dict([(int(u['id']), u) for u in test_users])
        user_ids = map(str, user_id_dict.keys())

        # use fql to figure out their names
        facebook = OpenFacebook(app_access_token)
        users = facebook.fql('SELECT uid, name FROM user WHERE uid in (%s)' %
                             ','.join(user_ids))
        users_dict = dict([(u['name'], u['uid']) for u in users])
        user_id = users_dict.get(name)

        if force_create and user_id:
            # we need the users access_token, the app access token doesn't
            # always work, seems to be a bug in the Facebook api
            test_user_data = user_id_dict[user_id]
            cls.delete_test_user(test_user_data['access_token'], user_id)
            user_id = None

        if user_id:
            # we found our user, extend the data a bit
            test_user_data = user_id_dict[user_id]
            test_user_data['name'] = name
            test_user = TestUser(test_user_data)
        else:
            # create the user
            test_user = cls.create_test_user(
                app_access_token, permissions, name)

        return test_user

    @classmethod
    def get_test_users(cls, app_access_token):
        kwargs = dict(access_token=app_access_token)
        path = '%s/accounts/test-users' % facebook_settings.FACEBOOK_APP_ID
        # retrieve all test users
        response = cls.request(path, **kwargs)
        test_users = response['data']
        return test_users

    @classmethod
    def delete_test_user(cls, app_access_token, test_user_id):
        kwargs = dict(access_token=app_access_token, method='delete')
        path = '%s/' % test_user_id

        # retrieve all test users
        response = cls.request(path, **kwargs)
        return response

    @classmethod
    def delete_test_users(cls, app_access_token):
        # retrieve all test users
        test_users = cls.get_test_users(app_access_token)
        test_user_ids = [u['id'] for u in test_users]
        for test_user_id in test_user_ids:
            cls.delete_test_user(app_access_token, test_user_id)


class OpenFacebook(FacebookConnection):

    '''
    The main api class, initialize using

    **Example**::

        graph = OpenFacebook(access_token)
        print graph.get('me')

    '''

    def __init__(self, access_token=None, prefetched_data=None,
                 expires=None, current_user_id=None):
        '''
            :param access_token:
                The facebook Access token
        '''
        self.access_token = access_token
        # extra data coming from signed cookies
        self.prefetched_data = prefetched_data

        # store to enable detection for offline usage
        self.expires = expires

        # hook to store the current user id if representing the
        # facebook connection to a logged in user :)
        self.current_user_id = current_user_id

    def __getstate__(self):
        '''
        Turns the object into something easy to serialize
        '''
        state = dict(
            access_token=self.access_token,
            prefetched_data=self.prefetched_data,
            expires=self.expires,
        )
        return state

    def __setstate__(self, state):
        '''
        Restores the object from the state dict
        '''
        self.access_token = state['access_token']
        self.prefetched_data = state['prefetched_data']
        self.expires = state['expires']

    def is_authenticated(self):
        '''
        Ask facebook if we have access to the users data

        :returns:  bool
        '''
        try:
            me = self.me()
        except facebook_exceptions.OpenFacebookException, e:
            if isinstance(e, facebook_exceptions.OAuthException):
                raise
            me = None
        authenticated = bool(me)
        return authenticated

    def get(self, path, **kwargs):
        '''
        Make a Facebook API call

        **Example**::

            open_facebook.get('me')
            open_facebook.get('me', fields='id,name')

        :param path:
            The path to use for making the API call

        :returns:  dict
        '''
        response = self.request(path, **kwargs)
        return response

    def get_many(self, *ids, **kwargs):
        '''
        Make a batched Facebook API call
        For multiple ids

        **Example**::

            open_facebook.get('me', 'starbucks')
            open_facebook.get('me', 'starbucks', fields='id,name')

        :param path:
            The path to use for making the API call

        :returns:  dict
        '''
        kwargs['ids'] = ','.join(ids)
        return self.request(**kwargs)

    def set(self, path, params=None, **post_data):
        '''
        Write data to facebook

        **Example**::

            open_facebook.set('me/feed', message='testing open facebook')

        :param path:
            The path to use for making the API call

        :param params:
            A dictionary of get params

        :param post_data:
            The kwargs for posting to facebook

        :returns:  dict
        '''
        assert self.access_token, 'Write operations require an access token'
        if not params:
            params = {}
        params['method'] = 'post'

        response = self.request(path, post_data=post_data, **params)
        return response

    def delete(self, path, *args, **kwargs):
        '''
        Delete the given bit of data

        **Example**::

            graph.delete(12345)

        :param path:
            the id of the element to remove

        '''

        kwargs['method'] = 'delete'
        self.request(path, *args, **kwargs)

    def fql(self, query, **kwargs):
        '''
        Runs the specified query against the Facebook FQL API.

        **Example**::

            open_facebook.fql('SELECT name FROM user WHERE uid = me()')

        :param query:
            The query to execute

        :param kwargs:
            Extra options to send to facebook

        :returns:  dict
        '''
        kwargs['q'] = query
        path = 'fql'

        response = self.request(path, **kwargs)

        # return only the data for backward compatability
        return response['data']

    def batch_fql(self, queries_dict):
        '''
        queries_dict a dict with the required queries
        returns the query results in:

        **Example**::

            response = facebook.batch_fql({
                name: 'SELECT uid, name, pic_square FROM user WHERE uid = me()',
                rsvp: 'SELECT uid, rsvp_status FROM event_member WHERE eid=12345678',
            })

            # accessing the results
            response['fql_results']['name']
            response['fql_results']['rsvp']

        :param queries_dict:
            A dictiontary of queries to execute

        :returns: dict
        '''
        query = json.dumps(queries_dict)
        query_results = self.fql(query)
        named_results = dict(
            [(r['name'], r['fql_result_set']) for r in query_results])

        return named_results

    def me(self):
        '''
        Cached method of requesting information about me
        '''
        me = getattr(self, '_me', None)
        if me is None:
            self._me = me = self.get('me')

        return me

    def permissions(self):
        '''
        Shortcut for self.get('me/permissions') with some extra parsing
        to turn it into a dictionary of booleans

        :returns: dict
        '''
        try:
            permissions = {}
            permissions_response = self.get('me/permissions')
            if permissions_response.get('data'):
                permissions = permissions_response['data'][0]
        except facebook_exceptions.OAuthException:
            permissions = {}
        permissions_dict = dict([(k, bool(int(v)))
                                 for k, v in permissions.items()
                                 if v == '1' or v == 1])
        return permissions_dict

    def has_permissions(self, required_permissions):
        '''
        Validate if all the required_permissions are currently given
        by the user

        **Example**::

            open_facebook.has_permissions(['publish_actions','read_stream'])

        :param required_permissions:
            A list of required permissions

        :returns: bool
        '''
        permissions_dict = self.permissions()
        # see if we have all permissions
        has_permissions = True
        for permission in required_permissions:
            if permission not in permissions_dict:
                has_permissions = False
        return has_permissions

    def my_image_url(self, size=None):
        '''
        Returns the image url from your profile
        Shortcut for me/picture

        :param size:
            the type of the image to request, see facebook for available formats

        :returns: string
        '''
        query_dict = QueryDict('', True)
        if size:
            query_dict['type'] = size
        query_dict['access_token'] = self.access_token

        url = '%sme/picture?%s' % (self.api_url, query_dict.urlencode())
        return url

    def request(self, path='', post_data=None, old_api=False, **params):
        api_base_url = self.old_api_url if old_api else self.api_url
        if getattr(self, 'access_token', None):
            params['access_token'] = self.access_token
        url = '%s%s?%s' % (api_base_url, path, urllib.urlencode(params))
        logger.info('requesting url %s', url)
        response = self._request(url, post_data)
        return response


class TestUser(object):

    '''
    Simple wrapper around test users
    '''

    def __init__(self, data):
        self.name = data['name']
        self.id = data['id']
        self.access_token = data['access_token']
        self.data = data

    def graph(self):
        graph = OpenFacebook(self.access_token)
        return graph

    def __repr__(self):
        return 'Test user %s' % self.name

from django.forms.util import ValidationError
from django_facebook import settings as facebook_settings, signals
from django_facebook.exceptions import FacebookException
from django_facebook.utils import get_user_model, mass_get_or_create, \
    cleanup_oauth_url, get_profile_model, parse_signed_request, hash_key, \
    try_get_profile, get_user_attribute
from open_facebook import exceptions as open_facebook_exceptions
from open_facebook.exceptions import OpenFacebookException
from open_facebook.utils import send_warning, validate_is_instance
import datetime
import json
import logging
try:
    from dateutil.parser import parse as parse_date
except ImportError:
    from django_facebook.utils import parse_like_datetime as parse_date


logger = logging.getLogger(__name__)


def require_persistent_graph(request, *args, **kwargs):
    '''
    Just like get_persistent graph, but instead of returning None
    raise an OpenFacebookException if we can't access facebook
    '''
    kwargs['raise_'] = True
    graph = get_persistent_graph(request, *args, **kwargs)
    if not graph:
        raise OpenFacebookException('please authenticate')
    return graph


def require_facebook_graph(request, *args, **kwargs):
    '''
    Just like get_facebook graph, but instead of returning None
    raise an OpenFacebookException if we can't access facebook
    '''
    kwargs['raise_'] = True
    graph = get_facebook_graph(request, *args, **kwargs)
    if not graph:
        raise OpenFacebookException('please authenticate')
    return graph


def get_persistent_graph(request, *args, **kwargs):
    '''
    Wraps itself around get facebook graph
    But stores the graph in the session, allowing usage across multiple
    pageviews.
    Note that Facebook session's expire at some point, you can't store this
    for permanent usage
    Atleast not without asking for the offline_access permission
    '''
    from open_facebook.api import OpenFacebook
    if not request:
        raise(ValidationError,
              'Request is required if you want to use persistent tokens')

    graph = None
    # some situations like an expired access token require us to refresh our
    # graph
    require_refresh = False
    code = request.REQUEST.get('code')
    if code:
        require_refresh = True

    local_graph = getattr(request, 'facebook', None)
    if local_graph:
        # gets the graph from the local memory if available
        graph = local_graph

    if not graph:
        # search for the graph in the session
        cached_graph_dict = request.session.get('graph_dict')
        if cached_graph_dict:
            graph = OpenFacebook()
            graph.__setstate__(cached_graph_dict)
            graph._me = None

    if not graph or require_refresh:
        # gets the new graph, note this might do token conversions (slow)
        graph = get_facebook_graph(request, *args, **kwargs)
        # if it's valid replace the old cache
        if graph is not None and graph.access_token:
            request.session['graph_dict'] = graph.__getstate__()

    # add the current user id and cache the graph at the request level
    _add_current_user_id(graph, request.user)
    request.facebook = graph

    return graph


def get_facebook_graph(request=None, access_token=None, redirect_uri=None, raise_=False):
    '''
    given a request from one of these
    - js authentication flow (signed cookie)
    - facebook app authentication flow (signed cookie)
    - facebook oauth redirect (code param in url)
    - mobile authentication flow (direct access_token)
    - offline access token stored in user profile

    returns a graph object

    redirect path is the path from which you requested the token
    for some reason facebook needs exactly this uri when converting the code
    to a token
    falls back to the current page without code in the request params
    specify redirect_uri if you are not posting and recieving the code
    on the same page
    '''
    # this is not a production flow, but very handy for testing
    if not access_token and request.REQUEST.get('access_token'):
        access_token = request.REQUEST['access_token']
    # should drop query params be included in the open facebook api,
    # maybe, weird this...
    from open_facebook import OpenFacebook, FacebookAuthorization
    from django.core.cache import cache
    expires = None
    if hasattr(request, 'facebook') and request.facebook:
        graph = request.facebook
        _add_current_user_id(graph, request.user)
        return graph

    # parse the signed request if we have it
    signed_data = None
    if request:
        signed_request_string = request.REQUEST.get('signed_data')
        if signed_request_string:
            logger.info('Got signed data from facebook')
            signed_data = parse_signed_request(signed_request_string)
        if signed_data:
            logger.info('We were able to parse the signed data')

    # the easy case, we have an access token in the signed data
    if signed_data and 'oauth_token' in signed_data:
        access_token = signed_data['oauth_token']

    if not access_token:
        # easy case, code is in the get
        code = request.REQUEST.get('code')
        if code:
            logger.info('Got code from the request data')

        if not code:
            # signed request or cookie leading, base 64 decoding needed
            cookie_name = 'fbsr_%s' % facebook_settings.FACEBOOK_APP_ID
            cookie_data = request.COOKIES.get(cookie_name)

            if cookie_data:
                signed_request_string = cookie_data
                if signed_request_string:
                    logger.info('Got signed data from cookie')
                signed_data = parse_signed_request(signed_request_string)
                if signed_data:
                    logger.info('Parsed the cookie data')
                # the javascript api assumes a redirect uri of ''
                redirect_uri = ''

            if signed_data:
                # parsed data can fail because of signing issues
                if 'oauth_token' in signed_data:
                    logger.info('Got access_token from parsed data')
                    # we already have an active access token in the data
                    access_token = signed_data['oauth_token']
                else:
                    logger.info('Got code from parsed data')
                    # no access token, need to use this code to get one
                    code = signed_data.get('code', None)

        if not access_token:
            if code:
                cache_key = hash_key('convert_code_%s' % code)
                access_token = cache.get(cache_key)
                if not access_token:
                    # exchange the code for an access token
                    # based on the php api
                    # https://github.com/facebook/php-sdk/blob/master/src/base_facebook.php
                    # create a default for the redirect_uri
                    # when using the javascript sdk the default
                    # should be '' an empty string
                    # for other pages it should be the url
                    if not redirect_uri:
                        redirect_uri = ''

                    # we need to drop signed_data, code and state
                    redirect_uri = cleanup_oauth_url(redirect_uri)

                    try:
                        logger.info(
                            'trying to convert the code with redirect uri: %s',
                            redirect_uri)
                        # This is realy slow, that's why it's cached
                        token_response = FacebookAuthorization.convert_code(
                            code, redirect_uri=redirect_uri)
                        expires = token_response.get('expires')
                        access_token = token_response['access_token']
                        # would use cookies instead, but django's cookie setting
                        # is a bit of a mess
                        cache.set(cache_key, access_token, 60 * 60 * 2)
                    except (open_facebook_exceptions.OAuthException, open_facebook_exceptions.ParameterException) as e:
                        # this sometimes fails, but it shouldnt raise because
                        # it happens when users remove your
                        # permissions and then try to reauthenticate
                        logger.warn('Error when trying to convert code %s',
                                    unicode(e))
                        if raise_:
                            raise
                        else:
                            return None
            elif request.user.is_authenticated():
                # support for offline access tokens stored in the users profile
                profile = try_get_profile(request.user)
                access_token = get_user_attribute(
                    request.user, profile, 'access_token')
                if not access_token:
                    if raise_:
                        message = 'Couldnt find an access token in the request or the users profile'
                        raise open_facebook_exceptions.OAuthException(message)
                    else:
                        return None
            else:
                if raise_:
                    message = 'Couldnt find an access token in the request or cookies'
                    raise open_facebook_exceptions.OAuthException(message)
                else:
                    return None

    graph = OpenFacebook(access_token, signed_data, expires=expires)
    # add user specific identifiers
    if request:
        _add_current_user_id(graph, request.user)

    return graph


def _add_current_user_id(graph, user):
    '''
    set the current user id, convenient if you want to make sure you
    fb session and user belong together
    '''
    if graph:
        graph.current_user_id = None

        if user.is_authenticated():
            profile = try_get_profile(user)
            facebook_id = get_user_attribute(user, profile, 'facebook_id')
            if facebook_id:
                graph.current_user_id = facebook_id


class FacebookUserConverter(object):

    '''
    This conversion class helps you to convert Facebook users to Django users

    Helps with
    - extracting and prepopulating full profile data
    - invite flows
    - importing and storing likes
    '''

    def __init__(self, open_facebook):
        from open_facebook.api import OpenFacebook
        self.open_facebook = open_facebook
        validate_is_instance(open_facebook, OpenFacebook)
        self._profile = None

    def is_authenticated(self):
        return self.open_facebook.is_authenticated()

    def facebook_registration_data(self, username=True):
        '''
        Gets all registration data
        and ensures its correct input for a django registration
        '''
        facebook_profile_data = self.facebook_profile_data()
        user_data = {}
        try:
            user_data = self._convert_facebook_data(
                facebook_profile_data, username=username)
        except OpenFacebookException as e:
            self._report_broken_facebook_data(
                user_data, facebook_profile_data, e)
            raise

        return user_data

    def facebook_profile_data(self):
        '''
        Returns the facebook profile data, together with the image locations
        '''
        if self._profile is None:
            profile = self.open_facebook.me()
            profile['image'] = self.open_facebook.my_image_url('large')
            profile['image_thumb'] = self.open_facebook.my_image_url()
            self._profile = profile
        return self._profile

    @classmethod
    def _convert_facebook_data(cls, facebook_profile_data, username=True):
        '''
        Takes facebook user data and converts it to a format for
        usage with Django
        '''
        user_data = facebook_profile_data.copy()
        profile = facebook_profile_data.copy()
        website = profile.get('website')
        if website:
            user_data['website_url'] = cls._extract_url(website)

        user_data['facebook_profile_url'] = profile.get('link')
        user_data['facebook_name'] = profile.get('name')
        if len(user_data.get('email', '')) > 75:
            # no more fake email accounts for facebook
            del user_data['email']

        gender = profile.get('gender', None)

        if gender == 'male':
            user_data['gender'] = 'm'
        elif gender == 'female':
            user_data['gender'] = 'f'

        user_data['username'] = cls._retrieve_facebook_username(user_data)
        user_data['password2'], user_data['password1'] = (
            cls._generate_fake_password(),) * 2  # same as double equal

        facebook_map = dict(birthday='date_of_birth',
                            about='about_me', id='facebook_id')
        for k, v in facebook_map.items():
            user_data[v] = user_data.get(k)
        user_data['facebook_id'] = int(user_data['facebook_id'])

        if not user_data['about_me'] and user_data.get('quotes'):
            user_data['about_me'] = user_data.get('quotes')

        user_data['date_of_birth'] = cls._parse_data_of_birth(
            user_data['date_of_birth'])

        if username:
            user_data['username'] = cls._create_unique_username(
                user_data['username'])

        # make sure the first and last name are not too long
        if 'first_name' in user_data:
            user_data['first_name'] = user_data['first_name'][:30]

        if 'last_name' in user_data:
            user_data['last_name'] = user_data['last_name'][:30]

        return user_data

    @classmethod
    def _extract_url(cls, text_url_field):
        '''
        >>> from django_facebook.api import FacebookApi
        >>> url_text = 'http://www.google.com blabla'
        >>> FacebookAPI._extract_url(url_text)
        u'http://www.google.com/'

        >>> url_text = 'http://www.google.com/'
        >>> FacebookAPI._extract_url(url_text)
        u'http://www.google.com/'

        >>> url_text = 'google.com/'
        >>> FacebookAPI._extract_url(url_text)
        u'http://google.com/'

        >>> url_text = 'http://www.fahiolista.com/www.myspace.com/www.google.com'
        >>> FacebookAPI._extract_url(url_text)
        u'http://www.fahiolista.com/www.myspace.com/www.google.com'
        '''
        import re
        text_url_field = text_url_field.encode('utf8')
        seperation = re.compile('[ ,;\n\r]+')
        try:
            parts = seperation.split(text_url_field)
        except TypeError:
            parts = seperation.split(text_url_field.decode())
        for part in parts:
            from django_facebook.utils import get_url_field
            url_check = get_url_field()
            try:
                clean_url = url_check.clean(part)
                return clean_url
            except ValidationError:
                continue

    @classmethod
    def _generate_fake_password(cls):
        '''
        Returns a random fake password
        '''
        import string
        from random import choice
        size = 9
        try:
            string.letters
        except AttributeError:
            string.letters = string.ascii_letters
        password = ''.join([choice(string.letters + string.digits)
                            for i in range(size)])
        return password.lower()

    @classmethod
    def _parse_data_of_birth(cls, data_of_birth_string):
        if data_of_birth_string:
            format = '%m/%d/%Y'
            try:
                parsed_date = datetime.datetime.strptime(
                    data_of_birth_string, format)
                return parsed_date
            except ValueError:
                # Facebook sometimes provides a partial date format
                # ie 04/07 (ignore those)
                if data_of_birth_string.count('/') != 1:
                    raise

    @classmethod
    def _report_broken_facebook_data(cls, facebook_data,
                                     original_facebook_data, e):
        '''
        Sends a nice error email with the
        - facebook data
        - exception
        - stacktrace
        '''
        from pprint import pformat
        data_dump = json.dumps(original_facebook_data)
        data_dump_python = pformat(original_facebook_data)
        message_format = 'The following facebook data failed with error %s' \
                         '\n\n json %s \n\n python %s \n'
        data_tuple = (unicode(e), data_dump, data_dump_python)
        message = message_format % data_tuple
        extra_data = {
            'data_dump': data_dump,
            'data_dump_python': data_dump_python,
            'facebook_data': facebook_data,
        }
        send_warning(message, **extra_data)

    @classmethod
    def _create_unique_username(cls, base_username):
        '''
        Check the database and add numbers to the username to ensure its unique
        '''
        usernames = list(
            get_user_model().objects.filter(
                username__istartswith=base_username
            ).values_list('username', flat=True))
        usernames_lower = [str(u).lower() for u in usernames]
        username = str(base_username)
        i = 1
        while base_username.lower() in usernames_lower:
            base_username = username + str(i)
            i += 1
        return base_username

    @classmethod
    def _retrieve_facebook_username(cls, facebook_data):
        '''
        Search for the username in 3 places
        - public profile
        - email
        - name
        '''
        username = None

        # start by checking the public profile link (your facebook username)
        link = facebook_data.get('link')
        if link:
            username = link.split('/')[-1]
            username = cls._make_username(username)
            if username and 'profilephp' in username:
                username = None

        # try the email adress next
        if not username and 'email' in facebook_data:
            username = cls._make_username(facebook_data.get(
                'email').split('@')[0])

        # last try the name of the user
        if not username or len(username) < 4:
            username = cls._make_username(facebook_data.get('name'))

        if not username:
            raise FacebookException('couldnt figure out a username')

        return username

    @classmethod
    def _make_username(cls, username):
        '''
        Slugify the username and replace - with _ to meet username requirements
        '''
        from django.template.defaultfilters import slugify
        from unidecode import unidecode
        slugified_name = slugify(unidecode(username)).replace('-', '_')

        # consider the username min and max constraints
        slugified_name = slugified_name[:30]
        if len(username) < 4:
            slugified_name = None

        return slugified_name

    def get_and_store_likes(self, user):
        '''
        Gets and stores your facebook likes to DB
        Both the get and the store run in a async task when
        FACEBOOK_CELERY_STORE = True
        '''
        if facebook_settings.FACEBOOK_CELERY_STORE:
            from django_facebook.tasks import get_and_store_likes
            get_and_store_likes.delay(user, self)
        else:
            self._get_and_store_likes(user)

    def _get_and_store_likes(self, user):
        likes = self.get_likes()
        stored_likes = self._store_likes(user, likes)
        return stored_likes

    def get_likes(self, limit=5000):
        '''
        Parses the facebook response and returns the likes
        '''
        likes_response = self.open_facebook.get('me/likes', limit=limit)
        likes = likes_response and likes_response.get('data')
        logger.info('found %s likes', len(likes))
        return likes

    def store_likes(self, user, likes):
        '''
        Given a user and likes store these in the db
        Note this can be a heavy operation, best to do it
        in the background using celery
        '''
        if facebook_settings.FACEBOOK_CELERY_STORE:
            from django_facebook.tasks import store_likes
            store_likes.delay(user, likes)
        else:
            self._store_likes(user, likes)

    @classmethod
    def _store_likes(self, user, likes):
        current_likes = inserted_likes = None

        if likes:
            from django_facebook.models import FacebookLike
            base_queryset = FacebookLike.objects.filter(user_id=user.id)
            global_defaults = dict(user_id=user.id)
            id_field = 'facebook_id'
            default_dict = {}
            for like in likes:
                name = like.get('name')
                created_time_string = like.get('created_time')
                created_time = None
                if created_time_string:
                    created_time = parse_date(like['created_time'])
                default_dict[like['id']] = dict(
                    created_time=created_time,
                    category=like.get('category'),
                    name=name
                )
            current_likes, inserted_likes = mass_get_or_create(
                FacebookLike, base_queryset, id_field, default_dict,
                global_defaults)
            logger.debug('found %s likes and inserted %s new likes',
                         len(current_likes), len(inserted_likes))

        # fire an event, so u can do things like personalizing the users' account
        # based on the likes
        signals.facebook_post_store_likes.send(sender=get_profile_model(),
                                               user=user, likes=likes, current_likes=current_likes,
                                               inserted_likes=inserted_likes,
                                               )

        return likes

    def get_and_store_friends(self, user):
        '''
        Gets and stores your facebook friends to DB
        Both the get and the store run in a async task when
        FACEBOOK_CELERY_STORE = True
        '''
        if facebook_settings.FACEBOOK_CELERY_STORE:
            from django_facebook.tasks import get_and_store_friends
            get_and_store_friends.delay(user, self)
        else:
            self._get_and_store_friends(user)

    def _get_and_store_friends(self, user):
        '''
        Getting the friends via fb and storing them
        '''
        friends = self.get_friends()
        stored_friends = self._store_friends(user, friends)
        return stored_friends

    def get_friends(self, limit=5000):
        '''
        Connects to the facebook api and gets the users friends
        '''
        friends = getattr(self, '_friends', None)
        if friends is None:
            friends_response = self.open_facebook.get('me/friends', limit=limit, fields='gender,name')

            friends = []
            for response_dict in friends_response.get('data'):
                response_dict['id'] = response_dict['id']
                friends.append(response_dict)

        logger.info('found %s friends', len(friends))

        return friends

    def store_friends(self, user, friends):
        '''
        Stores the given friends locally for this user
        Quite slow, better do this using celery on a secondary db
        '''
        if facebook_settings.FACEBOOK_CELERY_STORE:
            from django_facebook.tasks import store_friends
            store_friends.delay(user, friends)
        else:
            self._store_friends(user, friends)

    @classmethod
    def _store_friends(self, user, friends):
        from django_facebook.models import FacebookUser
        current_friends = inserted_friends = None

        # store the users for later retrieval
        if friends:
            # see which ids this user already stored
            base_queryset = FacebookUser.objects.filter(user_id=user.id)
            # if none if your friend have a gender clean the old data
            genders = FacebookUser.objects.filter(
                user_id=user.id, gender__in=('M', 'F')).count()
            if not genders:
                FacebookUser.objects.filter(user_id=user.id).delete()

            global_defaults = dict(user_id=user.id)
            default_dict = {}
            gender_map = dict(female='F', male='M')
            gender_map['male (hidden)'] = 'M'
            gender_map['female (hidden)'] = 'F'
            for f in friends:
                name = f.get('name')
                gender = None
                if f.get('sex'):
                    gender = gender_map[f.get('sex')]
                default_dict[str(f['id'])] = dict(name=name, gender=gender)
            id_field = 'facebook_id'

            current_friends, inserted_friends = mass_get_or_create(
                FacebookUser, base_queryset, id_field, default_dict,
                global_defaults)
            logger.debug('found %s friends and inserted %s new ones',
                         len(current_friends), len(inserted_friends))

        # fire an event, so u can do things like personalizing suggested users
        # to follow
        signals.facebook_post_store_friends.send(sender=get_profile_model(),
                                                 user=user, friends=friends, current_friends=current_friends,
                                                 inserted_friends=inserted_friends,
                                                 )

        return friends

    def registered_friends(self, user):
        '''
        Returns all profile models which are already registered on your site
        and a list of friends which are not on your site
        '''
        profile_class = get_profile_model()
        friends = self.get_friends(limit=1000)

        if friends:
            friend_ids = [f['id'] for f in friends]
            friend_objects = profile_class.objects.filter(
                facebook_id__in=friend_ids).select_related('user')
            registered_ids = [f.facebook_id for f in friend_objects]
            new_friends = [f for f in friends if f['id'] not in registered_ids]
        else:
            new_friends = []
            friend_objects = profile_class.objects.none()

        return friend_objects, new_friends

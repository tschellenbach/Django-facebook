from django.conf import settings
from django.core.mail import mail_admins
from django.forms.util import ValidationError
from django.utils import simplejson as json
from django_facebook import settings as facebook_settings
from django_facebook.utils import mass_get_or_create
from open_facebook.exceptions import OpenFacebookException
import datetime
import hashlib
import hmac
import logging
import sys
from django.http import QueryDict

logger = logging.getLogger(__name__)


def get_persistent_graph(request, *args, **kwargs):
    '''
    Wraps itself around get facebook graph
    But stores the graph in the session, allowing usage across multiple pageviews
    Note that Facebook session's expire at some point, you can't store this for permanent usage
    Atleast not without asking for the offline_access permission
    '''
    if not request:
        raise ValidationError, 'Request is required if you want to use persistent tokens'
    
    #get the new graph
    facebook_open_graph = get_facebook_graph(request, *args, **kwargs)
    
    #if it's valid replace the old cache
    if facebook_open_graph.access_token:
        request.session['facebook_open_graph'] = facebook_open_graph
    else:
        facebook_open_graph_cached = request.session.get('facebook_open_graph')
        if facebook_open_graph_cached:
            facebook_open_graph_cached._me = None
        facebook_open_graph = facebook_open_graph_cached   
        
    return facebook_open_graph
        
    

def get_facebook_graph(request=None, access_token=None, redirect_uri=None):
    '''
    given a request from one of these
    - js authentication flow (signed cookie)
    - facebook app authentication flow (signed cookie)
    - facebook oauth redirect (code param in url)
    - mobile authentication flow (direct access_token)
    
    returns a graph object
    
    redirect path is the path from which you requested the token
    for some reason facebook needs exactly this uri when converting the code
    to a token
    falls back to the current page without code in the request params
    specify redirect_uri if you are not posting and recieving the code on the same page
    '''
    #should drop query params be included in the open facebook api, maybe, weird this...
    DROP_QUERY_PARAMS = ['code','signed_request','state']
    from open_facebook import OpenFacebook, FacebookAuthorization
    parsed_data = None
        
    if not access_token:
        #easy case, code is in the get
        code = request.REQUEST.get('code')
        
        if not code:
            #signed request or cookie leading, base 64 decoding needed
            signed_data = request.REQUEST.get('signed_request')
            cookie_name = 'fbsr_%s' % facebook_settings.FACEBOOK_APP_ID
            cookie_data = request.COOKIES.get(cookie_name)
            if cookie_data:
                signed_data = cookie_data
                #the javascript api assumes a redirect uri of ''
                redirect_uri = ''
            if signed_data:
                parsed_data = FacebookAuthorization.parse_signed_data(signed_data)
                if 'oauth_token' in parsed_data:
                    # we already have an active access token in the data
                    access_token = parsed_data['oauth_token']
                else:
                    # no access token, need to use this code to get one
                    code = parsed_data['code']

        if not access_token:
            #exchange the code for an access token
            #based on the php api 
            #https://github.com/facebook/php-sdk/blob/master/src/base_facebook.php
            #we need to drop signed_request, code and state
            if redirect_uri is None:
                query_dict_items = [(k,v) for k, v in request.GET.items() if k not in DROP_QUERY_PARAMS]
                new_query_dict = QueryDict('', True)
                new_query_dict.update(dict(query_dict_items))
                #TODO support http and https
                redirect_uri = 'http://' + request.META['HTTP_HOST'] + request.path
                if new_query_dict:
                    redirect_uri += '?%s' % new_query_dict.urlencode()
            token_response = FacebookAuthorization.convert_code(code, redirect_uri=redirect_uri)
            access_token = token_response['access_token']
        
    facebook_open_graph = OpenFacebook(access_token, parsed_data)
    
    return facebook_open_graph


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
        assert isinstance(open_facebook, OpenFacebook)
        self._profile = None

    def is_authenticated(self):
        return self.open_facebook.is_authenticated()

    def facebook_registration_data(self):
        '''
        Gets all registration data
        and ensures its correct input for a django registration
        '''
        facebook_profile_data = self.facebook_profile_data()
        user_data = {}
        try:
            user_data = self._convert_facebook_data(facebook_profile_data)
        except OpenFacebookException, e:
            self._report_broken_facebook_data(user_data, facebook_profile_data, e)
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
    def _convert_facebook_data(cls, facebook_profile_data):
        '''
        Takes facebook user data and converts it to a format for usage with Django
        '''
        user_data = facebook_profile_data.copy()
        profile = facebook_profile_data.copy()
        website = profile.get('website')
        if website:
            user_data['website_url'] = cls._extract_url(website)
            
        user_data['facebook_profile_url'] = profile.get('link')
        user_data['facebook_name'] = profile.get('name')
        if len(user_data.get('email', '')) > 75:
            #no more fake email accounts for facebook
            del user_data['email']
        
        gender = profile.get('gender', None)
         
        if gender == 'male':
            user_data['gender'] = 'm'
        elif gender == 'female':
            user_data['gender'] = 'f'

        user_data['username'] = cls._retrieve_facebook_username(user_data)
        user_data['password2'] = user_data['password1'] = cls._generate_fake_password()

        facebook_map = dict(birthday='date_of_birth', about='about_me', id='facebook_id')
        for k, v in facebook_map.items():
            user_data[v] = user_data.get(k)

        if not user_data['about_me'] and user_data.get('quotes'):
            user_data['about_me'] = user_data.get('quotes')
            
        user_data['date_of_birth'] = cls._parse_data_of_birth(user_data['date_of_birth'])
        

        user_data['username'] = cls._create_unique_username(user_data['username'])

        return user_data

    @classmethod
    def _extract_url(cls, text_url_field):
        '''
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
        
        >>> url_text = u"""http://fernandaferrervazquez.blogspot.com/\r\nhttp://twitter.com/fferrervazquez\r\nhttp://comunidad.redfashion.es/profile/fernandaferrervazquez\r\nhttp://www.facebook.com/group.php?gid3D40257259997&ref3Dts\r\nhttp://fernandaferrervazquez.spaces.live.com/blog/cns!EDCBAC31EE9D9A0C!326.trak\r\nhttp://www.linkedin.com/myprofile?trk3Dhb_pro\r\nhttp://www.youtube.com/account#profile\r\nhttp://www.flickr.com/\r\n Mi galer\xeda\r\nhttp://www.flickr.com/photos/wwwfernandaferrervazquez-showroomrecoletacom/ \r\n\r\nhttp://www.facebook.com/pages/Buenos-Aires-Argentina/Fernanda-F-Showroom-Recoleta/200218353804?ref3Dts\r\nhttp://fernandaferrervazquez.wordpress.com/wp-admin/"""        
        >>> FacebookAPI._extract_url(url_text)
        u'http://fernandaferrervazquez.blogspot.com/a'
        '''
        import re
        text_url_field = text_url_field.encode('utf8')
        seperation = re.compile('[ ,;\n\r]+')
        parts = seperation.split(text_url_field)
        for part in parts:
            from django.forms import URLField
            url_check = URLField(verify_exists=False)
            try:
                clean_url = url_check.clean(part)
                return clean_url
            except ValidationError, e:
                continue

    @classmethod
    def _generate_fake_password(cls):
        '''
        Returns a random fake password
        '''
        import string
        from random import choice
        size = 9
        password = ''.join([choice(string.letters + string.digits) for i in range(size)])
        return password.lower()


    @classmethod
    def _parse_data_of_birth(cls, data_of_birth_string):
        if data_of_birth_string:
            format = '%m/%d/%Y'
            try:
                parsed_date = datetime.datetime.strptime(data_of_birth_string, format)
                return parsed_date
            except ValueError:
                #Facebook sometimes provides a partial date format ie 04/07 (ignore those)
                if data_of_birth_string.count('/') != 1:
                    raise

    @classmethod
    def _report_broken_facebook_data(cls, facebook_data, original_facebook_data, e):
        '''
        Sends a nice error email with the 
        - facebook data
        - exception
        - stacktrace
        '''
        from pprint import pformat
        data_dump = json.dumps(original_facebook_data)
        data_dump_python = pformat(original_facebook_data)
        message_format = 'The following facebook data failed with error %s\n\n json %s \n\n python %s \n'
        data_tuple = (unicode(e), data_dump, data_dump_python)
        
        logger.error(message_format % data_tuple,
            exc_info=sys.exc_info(), extra={
            'data': {
                 'data_dump': data_dump,
                 'data_dump_python': data_dump_python,
                 'facebook_data': facebook_data,
                 'body': message_format % data_tuple,
             }
        })

    @classmethod
    def _create_unique_username(cls, base_username):
        '''
        Check the database and add numbers to the username to ensure its unique
        '''
        from django.contrib.auth.models import User
        usernames = list(User.objects.filter(username__istartswith=base_username).values_list('username', flat=True))
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
        link = facebook_data.get('link')
        if link:
            username = link.split('/')[-1]
            username = cls._username_slugify(username)
        if 'profilephp' in username:
            username = None

        if not username and 'email' in facebook_data:
            username = cls._username_slugify(facebook_data.get('email').split('@')[0])
        
        if not username or len(username) < 4:
            username = cls._username_slugify(facebook_data.get('name'))

        return username

    @classmethod
    def _username_slugify(cls, username):
        '''
        Slugify the username and replace - with _ to meet username requirements
        '''
        from django.template.defaultfilters import slugify
        return slugify(username).replace('-', '_')
    
    def get_likes(self, limit=1000):
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
        Note this can be a heavy operation, best to do it in the background using celery
        '''
        if facebook_settings.FACEBOOK_CELERY_STORE:
            from django_facebook.tasks import store_likes
            store_likes(user, likes)
        else:
            self._store_likes(user, likes)
        
    @classmethod
    def _store_likes(self, user, likes):
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
                    created_time = datetime.datetime.strptime(like['created_time'], "%Y-%m-%dT%H:%M:%S+0000")
                default_dict[like['id']] = dict(
                    created_time=created_time,
                    category=like.get('category'),
                    name=name
                )
            current_likes, inserted_likes = mass_get_or_create(
                FacebookLike, base_queryset, id_field, default_dict, global_defaults
            )
            logger.debug('found %s likes and inserted %s new likes', len(current_likes), len(inserted_likes))
               
        return likes
    
    def get_friends(self, limit=1000):
        '''
        Connects to the facebook api and gets the users friends
        '''
        friends = getattr(self, '_friends', None)
        if friends is None:
            friends_response = self.open_facebook.get('me/friends', limit=limit)
            friends = friends_response and friends_response.get('data')
        
        logger.info('found %s friends', len(friends))
        
        return friends
    
    def store_friends(self, user, friends):
        '''
        Stores the given friends locally for this user
        Quite slow, better do this using celery on a secondary db
        '''
        if facebook_settings.FACEBOOK_CELERY_STORE:
            from django_facebook.tasks import store_friends
            store_friends(user, friends)
        else:
            self._store_friends(user, friends)
        
    @classmethod
    def _store_friends(self, user, friends):
        from django_facebook.models import FacebookUser
        #store the users for later retrieval
        if friends:
            #see which ids this user already stored
            base_queryset = FacebookUser.objects.filter(user_id=user.id)
            global_defaults = dict(user_id=user.id)
            default_dict = {}
            for f in friends:
                name = f.get('name')
                default_dict[f['id']] = dict(name=name)
            id_field = 'facebook_id'

            current_friends, inserted_friends = mass_get_or_create(
                FacebookUser, base_queryset, id_field, default_dict, global_defaults
            )
            logger.debug('found %s friends and inserted %s new ones', len(current_friends), len(inserted_friends))
                    
        return friends
    
    def registered_friends(self, user):
        '''
        Returns all profile models which are already registered on your site
        
        and a list of friends which are not on your site
        '''
        from django_facebook.utils import get_profile_class
        profile_class = get_profile_class()
        friends = self.get_friends(limit=1000)
        
        if friends:
            friend_ids = [f['id'] for f in friends]
            friend_objects = profile_class.objects.filter(facebook_id__in=friend_ids).select_related('user')
            registered_ids = [f.facebook_id for f in friend_objects]
            new_friends = [f for f in friends if f['id'] not in registered_ids]
        else:
            new_friends = []
            friend_objects = profile_class.objects.none()
            
        return friend_objects, new_friends
    

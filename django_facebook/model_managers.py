from django.db.models.query_utils import Q
from django.core.cache import cache
from django.db import models
from django_facebook import signals
from django.contrib import auth
from django_facebook.exceptions import IncompleteProfileError
from django.forms import ValidationError
import operator
import random
import datetime

from django.contrib.auth.models import User

class FacebookField(object):
    def __init__(self):
        self.required = True

class FacebookQueryField(FacebookField):
    def __init__(self, path, key=None, required=True, cast=None):
        self.path = path
        self.key = key
        self.required = required
        self.cast = cast
        
    def __call__(self, setup_obj):
        
        path_data = setup_obj._get_path(self.path)
        if self.key:
            ret_val = path_data.get(self.key)
        else:
            ret_val = path_data
        
        if self.cast:
            try:
                ret_val = self.cast(ret_val)
            except:
                ValueError("%r cannot be casted to %r" % 
                        (ret_val, self.cast))
        
        return ret_val

class FacebookImageField(FacebookField):
    def __init__(self, size=None):
        self.size = size
        self.required = False
    
    def __call__(self, setup_obj):
        return setup_obj.fb.my_image_url(self.size)

class FacebookUsernameField(FacebookField):
        
    def __call__(self, setup_obj):
        me = setup_obj._get_path("me/")
        for name in ["username", "link", "email", "name"]:
            username = getattr(self, "try_%s" % name)(me)
            if not username:
                continue
            if not self.check_unique(username):
                return username
    
    def try_username(self, me):
        username = me.get('username')
        if username:
            return self._username_slugify(username)
        
    def try_link(self, me):
        link = me.get("link")
        if link:
            username = link.split('/')[-1]
            username = self._username_slugify(username)

            if 'profilephp' not in username:
                return username
    
    def try_email(self, me):
        username = me.get("email").split("@")[0]
        if username:
            return self._username_slugify(username)
        
    def try_name(self, me):
        username = me.get("name")
        return self._username_slugify(username)
    
    def _username_slugify(self, username):
        '''
        Slugify the username and replace - with _ to meet username requirements
        '''
        from django.template.defaultfilters import slugify
        slugified_name = slugify(username).replace('-', '_')
        slugified_name = slugified_name[:30]
        slugified_name = slugified_name.lower()
        return slugified_name
    
    def check_unique(self, username):
        return User.objects.filter(username=username).exists()

class FacebookPasswordField(FacebookField):
    
    def __call__(self, setup_obj):
        import string
        from random import choice
        size = 9
        password = ''.join([choice(string.letters + string.digits)
                            for i in range(size)])
        return password.lower()

class FacebookAccessTokenField(FacebookField):
    
    def __call__(self, setup_obj):
        return setup_obj.fb.access_token

class FacebookFieldSetup(object):
    USER_DATA = ["username", "email", "password"]
    
    username = FacebookUsernameField()
    password = FacebookPasswordField()
    email = FacebookQueryField('me/', 'email')
    
    about_me = FacebookQueryField('me/', 'about', required=False)
    facebook_id = FacebookQueryField('me/', 'id', cast=int)
    access_token = FacebookAccessTokenField()
    facebook_name = FacebookQueryField('me/', 'name')
    facebook_profile_url = FacebookQueryField('me/', 'link')
    website_url = FacebookQueryField('me/', 'website', required=False)
    image = FacebookImageField('large')
    date_of_birth = FacebookQueryField('me/', 'birthday', required=False)
    gender = FacebookQueryField('me/', 'gender', required=False)
    raw_data = FacebookQueryField('me/', required=False)
    
    def __init__(self):
        self.path_cache = {}
        self.fb = None
        
    def _get_path(self, path):
        path_data = self.path_cache.get(path)
        if path_data is None:
            path_data = self.fb.get(path)
            self.path_cache[path] = path_data.copy()
        return path_data
    
    def _get_setup_data(self, fb):
        self.fb = fb
        user_data = {}
        profile_data = {}
        for name, field in self.__class__.__dict__.iteritems():
            if isinstance(field, FacebookField):

                data = field(self)
                if hasattr(self, "alter_%s" % name):
                    data = getattr(self, "alter_%s" % name)(data)
                
                if hasattr(self, "verify_%s" % name):
                    data = getattr(self, "verify_%s" % name)(data)

                if getattr(field, "required", None) and data is None:
                    raise IncompleteProfileError("Field %s is required" % name)
                
                if name not in self.USER_DATA:
                    profile_data[name] = data
                else:
                    user_data[name] = data
        return user_data, profile_data
    
    
    def alter_about_me(self, data):
        if data is None:
            return self._get_path('me/').get('quotes')
        return data
    
    def alter_date_of_birth(self, data_of_birth_string):
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
                
    def alter_gender(self, gender):
        try:
            symbol = gender[0]
            if symbol in ["m", "f"]:
                return symbol 
        except:
            pass
    
    def alter_website(self, website):
        import re
        website = website.encode('utf8')
        seperation = re.compile('[ ,;\n\r]+')
        parts = seperation.split(website)
        for part in parts:
            from django.forms import URLField
            url_check = URLField(verify_exists=False)
            try:
                clean_url = url_check.clean(part)
                return clean_url
            except ValidationError:
                continue
            
    
    def verify_email(self, email):
        if self._get_path('me/')["verified"]:
            return email
         
        
class FacebookProfileManager(models.Manager):
    setup_object = FacebookFieldSetup()
    
    def create_facebook_user(self, user_data=None, profile_data=None):
        new_user = auth.models.User.objects.create_user(
                **self.get_for_creation(user_data)
                )
        signals.facebook_user_registered.send(sender=auth.models.User,
            user=new_user, facebook_data=profile_data)

        new_user = self.update_user(new_user, user_data, profile_data)
    
        return new_user   

    def get_profile_data(self, fb):
        return self.setup_object._get_setup_data(fb)

    def get_for_creation(self, data):
        return { data[key] for key in ["username", "email", "password"]}
    
    
    def remove_old_connections(self, facebook_id, current_user_id=None):
        other_facebook_accounts = self.filter(
                facebook_id=facebook_id)
        if current_user_id:
            other_facebook_accounts = other_facebook_accounts.exclude(
                user__id=current_user_id)
        other_facebook_accounts.update(facebook_id=None)
    
    def update_user(self, user, user_data=None, profile_data=None,
            overwrite=True):
        '''
        Updates the user and his/her profile with the data from facebook
        '''
        # if you want to add fields to ur user model instead of the
        # profile thats fine
        # partial support (everything except raw_data and facebook_id is included)
        user_data.pop("password")
        user_dirty = profile_dirty = False
        profile = user.get_profile()
    
        signals.facebook_pre_update.send(sender=self.model,
            profile=profile, facebook_data=profile_data)
    
        #set the facebook id and make sure we are the only user with this id
        facebook_id_changed = profile_data['facebook_id'] != profile.facebook_id
        overwrite_allowed = overwrite or not profile.facebook_id
    
        #update the facebook id and access token
        if facebook_id_changed and overwrite_allowed:
            #when not overwriting we only update if there is no profile.facebook_id
#            logger.info('profile facebook id changed from %s to %s',
#                        repr(profile_data['facebook_id']),
#                        repr(profile.facebook_id))
            profile.facebook_id = profile_data['facebook_id']
            profile_dirty = True
            self.remove_old_connections(profile.facebook_id, user.id)
    
        #update all fields on both user and profile
        for fname, value in user_data.iteritems():
            if hasattr(user, fname):
                cur_val = getattr(user, fname, None)
                if cur_val != value:
                    setattr(user, fname, value)
                    user_dirty = True
        
        for fname, value in user_data.iteritems():
            if hasattr(profile, fname):
                cur_val = getattr(profile, fname, None)
                if cur_val != value:
                    setattr(profile, fname, value)
                    profile_dirty = True 
        
    
#        image_url = profile_data['image']
#        if hasattr(profile, 'image') and not profile.image:
#            profile_dirty = _update_image(profile, image_url)
    
        #save both models if they changed
        if user_dirty:
            user.save()
        if profile_dirty:
            profile.save()
    
        signals.facebook_post_update.send(sender=self.model(),
            profile=profile, facebook_data=profile_data)
    
        return user

class FacebookUserManager(models.Manager):
    def find_users(self, queries, base_queryset=None):
        '''
        Queries, a list of search queries
        Base Queryset, the base queryset in which we are searching
        '''
        if base_queryset is None:
            base_queryset = self.all()
        filters = []
        for query in queries:
            match = Q(name__istartswith=query) | Q(name__icontains=' %s' % query)
            filters.append(match)
                
        users = base_queryset.filter(reduce(operator.and_, filters))

        return users
    
    def random_facebook_friends(self, user, gender=None, limit=3):
        '''
        Returns a random sample of your FB friends
        
        Limit = Number of friends
        Gender = None, M or F 
        '''
        assert gender in (None, 'M', 'F'), 'Gender %s wasnt recognized' % gender
        
        from django_facebook.utils import get_profile_class
        facebook_cache_key = 'facebook_users_%s' % user.id
        non_members = cache.get(facebook_cache_key)
        profile_class = get_profile_class()
        if not non_members:
            facebook_users = list(self.filter(user_id=user.id, gender=gender)[:50])
            facebook_ids = [u.facebook_id for u in facebook_users]
            members = list(profile_class.objects.filter(facebook_id__in=facebook_ids).select_related('user'))
            member_ids = [p.facebook_id for p in members]
            non_members = [u for u in facebook_users if u.facebook_id not in member_ids]
            
            cache.set(facebook_cache_key, non_members, 60 * 60)
            
        random_limit = min(len(non_members), 3)
        random_facebook_users = []
        if random_limit:
            random_facebook_users = random.sample(non_members, random_limit)
            
        return random_facebook_users
        

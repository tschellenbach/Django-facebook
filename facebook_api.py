from django_facebook.facebook import GraphAPI, GraphAPIError
from django.core.mail import send_mail, mail_admins
from django_facebook import settings as facebook_settings
import datetime
from django.forms.util import ValidationError


class FacebookAPI(GraphAPI):
    '''
    Wrapper around the default facebook api with
    - support for creating django users
    - caches registration and profile data, ensuring
    efficient use of facebook connections
    '''
    def __init__(self, user):
        self._is_authenticated = None
        self._profile = None
        self.access_token = False
        if user:
            GraphAPI.__init__(self, user['access_token'])


    def is_authenticated(self):
        '''
        Checks if the cookie/post data provided is actually valid
        '''
        if self._is_authenticated is None:
            try:
                self.facebook_profile_data()
                self._is_authenticated = True
            except GraphAPIError, e:
                self._is_authenticated = False

        return self._is_authenticated


    def facebook_profile_data(self):
        '''
        Returns the facebook profile data, together with the image locations
        '''
        if self._profile is None:
            profile = self.get_object('me')
            profile['image'] = 'https://graph.facebook.com/me/picture?type=large&access_token=%s' % self.access_token
            profile['image_thumb'] = 'https://graph.facebook.com/me/picture?access_token=%s' % self.access_token
            self._profile = profile
        return self._profile


    def facebook_registration_data(self):
        '''
        Gets all registration data
        and ensures its correct input for a django registration
        '''
        if self.is_authenticated():
            facebook_profile_data = self.facebook_profile_data()
            user_data = {}
            try:
                user_data = FacebookAPI._convert_facebook_data(facebook_profile_data)
            except Exception, e:
                FacebookAPI._report_broken_facebook_data(user_data, facebook_profile_data, e)

        return user_data

    @classmethod
    def _convert_facebook_data(cls, facebook_profile_data):
        '''
        Takes facebook user data and converts it to a format for usage with Django
        '''
        user_data = facebook_profile_data.copy()
        profile = facebook_profile_data.copy()
        user_data['website_url'] = cls._extract_url(profile.get('website'))
        user_data['facebook_profile_url'] = profile.get('link')
        user_data['facebook_name'] = profile.get('name')
        if len(user_data.get('email', '')) > 75:
            #no more fake email accounts for facebook
            del user_data['email']
        

        user_data['username'] = FacebookAPI._retrieve_facebook_username(user_data)
        if facebook_settings.FACEBOOK_FAKE_PASSWORD:
            user_data['password2'] = user_data['password1'] = FacebookAPI._generate_fake_password()

        facebook_map = dict(birthday='date_of_birth', about='about_me', id='facebook_id')
        for k, v in facebook_map.items():
            user_data[v] = user_data.get(k)

        user_data['date_of_birth'] = FacebookAPI._parse_data_of_birth(user_data['date_of_birth'])

        user_data['username'] = FacebookAPI._create_unique_username(user_data['username'])

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
        '''
        import re
        text_url_field = str(text_url_field)
        seperation = re.compile('[ |,|;]+')
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
        import cjson
        message = 'The following facebook data failed %s with error %s' % (cjson.encode(original_facebook_data), unicode(e))
        mail_admins('Broken facebook data', message)


    @classmethod
    def _create_unique_username(cls, base_username):
        '''
        Check the database and add numbers to the username to ensure its unique
        '''
        from django.contrib.auth.models import User
        usernames = User.objects.filter(username__istartswith=base_username).values_list('username', flat=True)
        username = base_username
        i = 1
        while base_username in usernames:
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

        if not username:
            if 'email' in facebook_data:
                username = cls._username_slugify(facebook_data.get('email').split('@')[0])
            else:
                username = cls._username_slugify(facebook_data.get('name'))

        return username


    @classmethod
    def _username_slugify(cls, username):
        '''
        Slugify the username and replace - with _ to meet username requirements
        '''
        from django.template.defaultfilters import slugify
        return slugify(username).replace('-', '_')

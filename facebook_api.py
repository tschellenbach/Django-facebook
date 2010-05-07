from django_facebook.facebook import GraphAPI, GraphAPIError
from django.core.mail import send_mail, mail_admins
from django_facebook import settings as facebook_settings


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
            profile['image'] = 'http://graph.facebook.com/me/picture?type=large&access_token=%s' % self.access_token
            profile['image_thumb'] = 'http://graph.facebook.com/me/picture?access_token=%s' % self.access_token
            self._profile = profile
        return self._profile


    def facebook_registration_data(self):
        '''
        Gets all registration data
        and ensures its correct input for a django registration
        '''
        facebook_data = {}
        original_facebook_data = {}
        if self.is_authenticated():
            profile = self.facebook_profile_data()
            try:
                facebook_data = profile.copy()
                original_facebook_data = profile.copy()
                facebook_data['website_url'] = profile.get('website')
                facebook_data['facebook_profile_url'] = profile.get('link')
                facebook_data['facebook_name'] = profile.get('name')


                facebook_data['username'] = FacebookAPI._retrieve_facebook_username(facebook_data)
                if facebook_settings.FACEBOOK_FAKE_PASSWORD:
                    facebook_data['password2'] = facebook_data['password1'] = FacebookAPI._generate_fake_password()

                facebook_map = dict(birthday='date_of_birth', about='about_me', id='facebook_id')
                for k, v in facebook_map.items():
                    facebook_data[v] = facebook_data.get(k)

                facebook_data['date_of_birth'] = FacebookAPI._parse_data_of_birth(facebook_data['date_of_birth'])

                facebook_data['username'] = FacebookAPI._create_unique_username(facebook_data['username'])
            except Exception, e:
                FacebookAPI._report_broken_facebook_data(facebook_data, original_facebook_data, e)

        return facebook_data


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
        import datetime
        format = '%m/%d/%Y'
        parsed_date = datetime.datetime.strptime(data_of_birth_string, format)
        return parsed_date


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

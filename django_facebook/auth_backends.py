from django.contrib.auth import models, backends
from django.db.utils import DatabaseError
from django_facebook.utils import get_profile_model
from django_facebook import settings as facebook_settings
from django_facebook.utils import get_user_model
from django.db.models.query_utils import Q
#from user import models as models_user


class FacebookBackend(backends.ModelBackend):
    def authenticate(self, facebook_id=None, facebook_email=None):
        '''
        Authenticate the facebook user by id OR facebook_email
        We filter using an OR to allow existing members to connect with
        their facebook ID using email.
        '''
        if facebook_id or facebook_email:
            profile_class = get_profile_model()
            profile_query = profile_class.objects.all().order_by('user')
            profile_query = profile_query.select_related('user')
            profile = None

            #filter on email or facebook id, two queries for better
            #queryplan with large data sets
            if facebook_id:
                profiles = profile_query.filter(facebook_id=facebook_id)[:1]
                profile = profiles[0] if profiles else None
            if profile is None and facebook_email:
                try:
                    profiles = profile_query.filter(
                        user__email__iexact=facebook_email)[:1]
                    profile = profiles[0] if profiles else None
                except DatabaseError:
                    try:
                        user = get_user_model(
                        ).objects.get(email=facebook_email)
                    except get_user_model().DoesNotExist:
                        user = None
                    profile = user.get_profile() if user else None

            if profile:
                # populate the profile cache while we're getting it anyway
                user = profile.user
                user._profile = profile
                if facebook_settings.FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN:
                    user.fb_update_required = True
                return user


class FacebookUserBackend(backends.ModelBackend):
    def authenticate(self, facebook_id=None, facebook_email=None):
        '''
        Authenticate the facebook user by id OR facebook_email
        We filter using an OR to allow existing members to connect with
        their facebook ID using email.
        
        This decorator works with django's custom user model
        '''
        user_model = get_user_model()
        if facebook_id or facebook_email:
            # match by facebook id or email
            facebook_id_match = Q(facebook_id=facebook_id)
            facebook_email_match = Q(email__iexact=facebook_email)
            authentication_condition = facebook_id_match | facebook_email_match
            
            # get the users in one query
            users = list(user_model.objects.filter(authentication_condition))
            
            # id matches vs email matches
            id_matches = [u for u in users if u.facebook_id == facebook_id]
            email_matches = [u for u in users if u.facebook_id != facebook_id]
            
            # error checking
            if len(id_matches) > 1:
                raise ValueError('found multiple facebook id matches. this shouldnt be allowed, check your unique constraints. users found %s' % users)
            
            # give the right user
            user = None
            if id_matches:
                user = id_matches[0]
            elif email_matches:
                user = email_matches[0]

            if facebook_settings.FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN:
                user.fb_update_required = True
            return user

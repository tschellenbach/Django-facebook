from django.conf import settings
from django.contrib.auth import models, backends
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q
import operator
from django_facebook.utils import get_profile_class
#from user import models as models_user


class FacebookBackend(backends.ModelBackend):
    def authenticate(self, facebook_id=None, facebook_email=None):
        '''
        Authenticate the facebook user by id OR facebook_email
        
        We filter using an OR to allow existing members to connect with their facebook ID using email.
        
        '''
        if facebook_id or facebook_email:
            profile_class = get_profile_class()
            profile_query = profile_class.objects.all().order_by('user')
            profile_query = profile_query.select_related('user')
            profile = None
            
            #filter on email or facebook id, two queries for better
            #queryplan with large data sets
            if facebook_id:
                profiles = profile_query.filter(facebook_id=facebook_id)[:1]
                profile = profiles[0] if profiles else None
            if profile is None and facebook_email:
                profiles = profile_query.filter(user__email__iexact=facebook_email)[:1]
                profile = profiles[0] if profiles else None

            if profile:
                # populate the profile cache while we're getting it anyway
                user = profile.user
                user._profile = profile
                return user
                

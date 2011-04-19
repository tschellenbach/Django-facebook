from django.conf import settings
from django.contrib.auth import models, backends
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q
import operator
#from user import models as models_user


class FacebookBackend(backends.ModelBackend):
    def authenticate(self, facebook_id=None, facebook_email=None):
        '''
        Authenticate the facebook user by id OR facebook_email
        
        We filter using an OR to allow existing members to connect with their facebook ID using email.
        
        '''
        #filter on email or facebook id
        filter_clause = []
        if facebook_id:
            filter_clause.append(Q(facebook_id=facebook_id))
        if facebook_email:
            filter_clause.append(Q(user__email__iexact=facebook_email))
        filter_clause = reduce(operator.or_, filter_clause) 

        #get the profile model and search for our user
        if facebook_id or facebook_email:
            #TODO: isn't there a dedicated function for this in django somewhere?
            profile_string = settings.AUTH_PROFILE_MODULE
            profile_model = profile_string.split('.')[-1]
            profile_class = ContentType.objects.get(model=profile_model.lower()).model_class()

            profiles = profile_class.objects.all()
            profiles = profiles.order_by('user')
            profiles = profiles.select_related('user')
            
            # Doing separate queries to get a better queryplan with large
            # databases
            if facebook_id:
                try:
                    profile = profiles.get(facebook_id=facebook_id)
                except profile_class.DoesNotExist:
                    profile = None

            if profile is None and facebook_email:
                try:
                    profile = profiles.get(user__email__iexact=facebook_email)
                except profile_class.DoesNotExist:
                    profile = None

            if profile:
                # populate the profile cache while we're getting it anyway
                user = profile.user
                user._profile = profile
                return user
                

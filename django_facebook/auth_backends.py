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
            filter_clause.append(Q(user__email=facebook_email))
        filter_clause = reduce(operator.or_, filter_clause) 

        #get the profile model and search for our user
        if filter_clause:
            #TODO: isn't there a dedicated function for this in django somewhere?
            profile_string = settings.AUTH_PROFILE_MODULE
            profile_model = profile_string.split('.')[-1]
            profile_class = ContentType.objects.get(model=profile_model.lower()).model_class()
            profiles = profile_class.objects.filter(filter_clause).order_by('user')[:1]
            if profiles:
                user = profiles[0].user
                return user
                

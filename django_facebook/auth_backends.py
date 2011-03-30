from django.conf import settings
from django.contrib.auth import models, backends
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q
#from user import models as models_user


class FacebookBackend(backends.ModelBackend):
    def authenticate(self, facebook_id=None, facebook_email=None):
        '''
        Authenticate the facebook user by id OR facebook_email
        '''
        filter_clause = False
        if facebook_id:
            filter_clause = Q(facebook_id=facebook_id)

        if facebook_email:
            email_filter = Q(user__email=facebook_email)
            if filter_clause:
                filter_clause |= email_filter
            else:
                filter_clause = email_filter

        if filter_clause:
            try:
                profile_string = settings.AUTH_PROFILE_MODULE
            except AttributeError:
                profile_string = None
            if profile_string:
                profile_model = profile_string.split('.')[-1]
                profile_class = ContentType.objects.get(model=profile_model.lower())
                profile = profile_class.get_object_for_this_type(filter_clause)
                #profiles = profile_class.objects.filter(filter_clause).order_by('user')[:1]
                if profile:
                    user = profile.user
                    return user
            else:
                raise KeyError

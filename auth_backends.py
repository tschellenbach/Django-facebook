from django.contrib.auth import models, backends
from user import models as models_user
from django.db.models.query_utils import Q


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
            profiles = models_user.Profile.objects.filter(filter_clause).order_by('user')[:1]
            if profiles:
                user = profiles[0].user
                return user




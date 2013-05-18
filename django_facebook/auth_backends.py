from django.contrib.auth import backends
from django.db.models.query_utils import Q
from django.db.utils import DatabaseError
from django_facebook import settings as facebook_settings
from django_facebook.utils import get_profile_model, is_user_attribute, \
    get_user_model
import operator


class FacebookBackend(backends.ModelBackend):

    '''
    Django Facebook authentication backend

    This backend hides the difference between authenticating with
    - a django 1.5 custom user model
    - profile models, which were used prior to 1.5

    **Example usage**

    >>> FacebookBackend().authenticate(facebook_id=myid)

    '''

    def authenticate(self, *args, **kwargs):
        '''
        Route to either the user or profile table depending on which type of user
        customization we are using
        (profile was used in Django < 1.5, user is the new way in 1.5 and up)
        '''
        user_attribute = is_user_attribute('facebook_id')
        if user_attribute:
            user = self.user_authenticate(*args, **kwargs)
        else:
            user = self.profile_authenticate(*args, **kwargs)
        return user

    def user_authenticate(self, facebook_id=None, facebook_email=None):
        '''
        Authenticate the facebook user by id OR facebook_email
        We filter using an OR to allow existing members to connect with
        their facebook ID using email.

        This decorator works with django's custom user model

        :param facebook_id:
            Optional string representing the facebook id.
        :param facebook_email:
            Optional string with the facebook email.

        :return: The signed in :class:`User`.
        '''
        user_model = get_user_model()
        if facebook_id or facebook_email:
            # match by facebook id or email
            auth_conditions = []
            if facebook_id:
                auth_conditions.append(Q(facebook_id=facebook_id))
            if facebook_email:
                auth_conditions.append(Q(email__iexact=facebook_email))
            # or the operations
            auth_condition = reduce(operator.or_, auth_conditions)

            # get the users in one query
            users = list(user_model.objects.filter(auth_condition))

            # id matches vs email matches
            id_matches = [u for u in users if u.facebook_id == facebook_id]
            email_matches = [u for u in users if u.facebook_id != facebook_id]

            # error checking
            if len(id_matches) > 1:
                raise ValueError(
                    'found multiple facebook id matches. this shouldnt be allowed, check your unique constraints. users found %s' % users)

            # give the right user
            user = None
            if id_matches:
                user = id_matches[0]
            elif email_matches:
                user = email_matches[0]

            if user and facebook_settings.FACEBOOK_FORCE_PROFILE_UPDATE_ON_LOGIN:
                user.fb_update_required = True
            return user

    def profile_authenticate(self, facebook_id=None, facebook_email=None):
        '''
        Authenticate the facebook user by id OR facebook_email
        We filter using an OR to allow existing members to connect with
        their facebook ID using email.

        :param facebook_id:
            Optional string representing the facebook id

        :param facebook_email:
            Optional string with the facebook email

        :return: The signed in :class:`User`.
        '''
        if facebook_id or facebook_email:
            profile_class = get_profile_model()
            profile_query = profile_class.objects.all().order_by('user')
            profile_query = profile_query.select_related('user')
            profile = None

            # filter on email or facebook id, two queries for better
            # queryplan with large data sets
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

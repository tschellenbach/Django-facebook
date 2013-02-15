from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.base import ModelBase
from django_facebook import model_managers, settings as facebook_settings
from open_facebook.utils import json, camel_to_underscore
from datetime import timedelta
from django_facebook.utils import compatible_datetime as datetime
from django_facebook.utils import get_user_model

import logging
import os
logger = logging.getLogger(__name__)


if facebook_settings.FACEBOOK_PROFILE_IMAGE_PATH:
    PROFILE_IMAGE_PATH = settings.FACEBOOK_PROFILE_IMAGE_PATH
else:
    PROFILE_IMAGE_PATH = os.path.join('images', 'facebook_profiles/%Y/%m/%d')


class FACEBOOK_OG_STATE:
    class NOT_CONNECTED:
        '''
        The user has not connected their profile with Facebook
        '''
        pass

    class CONNECTED:
        '''
        The user has connected their profile with Facebook, but isn't
        setup for Facebook sharing
        - sharing is either disabled
        - or we have no valid access token
        '''
        pass

    class SHARING(CONNECTED):
        '''
        The user is connected to Facebook and sharing is enabled
        '''
        pass


class BaseFacebookProfileModel(models.Model):
    '''
    Abstract class to add to your profile model.
    NOTE: If you don't use this this abstract class, make sure you copy/paste
    the fields in.
    '''
    about_me = models.TextField(blank=True, null=True)
    facebook_id = models.BigIntegerField(blank=True, unique=True, null=True)
    access_token = models.TextField(
        blank=True, help_text='Facebook token for offline access', null=True)
    facebook_name = models.CharField(max_length=255, blank=True, null=True)
    facebook_profile_url = models.TextField(blank=True, null=True)
    website_url = models.TextField(blank=True, null=True)
    blog_url = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=(
        ('m', 'Male'), ('f', 'Female')), blank=True, null=True)
    raw_data = models.TextField(blank=True, null=True)
    facebook_open_graph = models.BooleanField(default=True, help_text='Determines if this user want to share via open graph')

    def __unicode__(self):
        return self.user.__unicode__()

    class Meta:
        abstract = True

    @property
    def facebook_og_state(self):
        if not self.facebook_id:
            state = FACEBOOK_OG_STATE.NOT_CONNECTED
        elif self.access_token and self.facebook_open_graph:
            state = FACEBOOK_OG_STATE.SHARING
        else:
            state = FACEBOOK_OG_STATE.CONNECTED
        return state

    def likes(self):
        likes = FacebookLike.objects.filter(user_id=self.user_id)
        return likes

    def friends(self):
        friends = FacebookUser.objects.filter(user_id=self.user_id)
        return friends

    def post_facebook_registration(self, request):
        '''
        Behaviour after registering with facebook
        '''
        from django_facebook.utils import next_redirect
        default_url = reverse('facebook_connect')
        response = next_redirect(request, default=default_url,
                                 next_key=['register_next', 'next'])
        response.set_cookie('fresh_registration', self.user_id)

        return response

    def disconnect_facebook(self):
        self.access_token = None
        self.facebook_id = None

    def clear_access_token(self):
        self.access_token = None
        self.save()

    def extend_access_token(self):
        '''
        https://developers.facebook.com/roadmap/offline-access-removal/
        We can extend the token only once per day
        Normal short lived tokens last 1-2 hours
        Long lived tokens (given by extending) last 60 days

        The token can be extended multiple times, supposedly on every visit
        '''
        logger.info('extending access token for user %s', self.user)
        results = None
        if facebook_settings.FACEBOOK_CELERY_TOKEN_EXTEND:
            from django_facebook import tasks
            tasks.extend_access_token.delay(self, self.access_token)
        else:
            results = self._extend_access_token(self.access_token)
        return results

    def _extend_access_token(self, access_token):
        from open_facebook.api import FacebookAuthorization
        results = FacebookAuthorization.extend_access_token(access_token)
        access_token = results['access_token']
        old_token = self.access_token
        token_changed = access_token != old_token
        message = 'a new' if token_changed else 'the same'
        log_format = 'Facebook provided %s token, which expires at %s'
        expires_delta = timedelta(days=60)
        logger.info(log_format, message, expires_delta)
        if token_changed:
            logger.info('Saving the new access token')
            self.access_token = access_token
            self.save()

        from django_facebook.signals import facebook_token_extend_finished
        facebook_token_extend_finished.send(sender=self, profile=self,
                                            token_changed=token_changed, old_token=old_token
                                            )

        return results

    def get_offline_graph(self):
        '''
        Returns a open facebook graph client based on the access token stored
        in the user's profile
        '''
        from open_facebook.api import OpenFacebook
        if self.access_token:
            graph = OpenFacebook(access_token=self.access_token)
            graph.current_user_id = self.facebook_id
            return graph


class FacebookProfileModel(BaseFacebookProfileModel):
    '''
    the image field really destroys the subclassability of an abstract model
    you always need to customize the upload settings and storage settings

    thats why we stick it in a separate class

    override the BaseFacebookProfile if you want to change the image
    '''
    image = models.ImageField(blank=True, null=True,
                              upload_to=PROFILE_IMAGE_PATH, max_length=255)

    class Meta:
        abstract = True


class FacebookUser(models.Model):
    '''
    Model for storing a users friends
    '''
    # in order to be able to easily move these to an another db,
    # use a user_id and no foreign key
    user_id = models.IntegerField()
    facebook_id = models.BigIntegerField()
    name = models.TextField(blank=True, null=True)
    gender = models.CharField(choices=(
        ('F', 'female'), ('M', 'male')), blank=True, null=True, max_length=1)

    objects = model_managers.FacebookUserManager()

    class Meta:
        unique_together = ['user_id', 'facebook_id']

    def __unicode__(self):
        return u'Facebook user %s' % self.name


class FacebookLike(models.Model):
    '''
    Model for storing all of a users fb likes
    '''
    # in order to be able to easily move these to an another db,
    # use a user_id and no foreign key
    user_id = models.IntegerField()
    facebook_id = models.BigIntegerField()
    name = models.TextField(blank=True, null=True)
    category = models.TextField(blank=True, null=True)
    created_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ['user_id', 'facebook_id']


class FacebookProfile(FacebookProfileModel):
    '''
    Not abstract version of the facebook profile model
    Use this by setting
    AUTH_PROFILE_MODULE = 'django_facebook.FacebookProfile'
    '''
    user = models.OneToOneField(get_user_model())


class BaseModelMetaclass(ModelBase):
    '''
    Cleaning up the table naming conventions
    '''

    def __new__(cls, name, bases, attrs):
        super_new = ModelBase.__new__(cls, name, bases, attrs)
        module_name = camel_to_underscore(name)

        app_label = super_new.__module__.split('.')[-2]
        db_table = '%s_%s' % (app_label, module_name)

        django_default = '%s_%s' % (app_label, name.lower())
        if not getattr(super_new._meta, 'proxy', False):
            db_table_is_default = django_default == super_new._meta.db_table
            #Don't overwrite when people customize the db_table
            if db_table_is_default:
                super_new._meta.db_table = db_table

        return super_new


class BaseModel(models.Model):
    '''
    Stores the fields common to all incentive models
    '''
    __metaclass__ = BaseModelMetaclass

    def __unicode__(self):
        '''
        Looks at some common ORM naming standards and tries to display those before
        default to the django default
        '''
        attributes = ['name', 'title', 'slug']
        name = None
        for a in attributes:
            if hasattr(self, a):
                name = getattr(self, a)
        if not name:
            name = repr(self.__class__)
        return name

    class Meta:
        abstract = True


class CreatedAtAbstractBase(BaseModel):
    '''
    Stores the fields common to all incentive models
    '''
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    #determine if we should clean this model
    auto_clean = False

    def save(self, *args, **kwargs):
        '''
        Allow for auto clean support
        '''
        if self.auto_clean:
            self.clean()
        saved = models.Model.save(self, *args, **kwargs)
        return saved

    def __unicode__(self):
        '''
        Looks at some common ORM naming standards and tries to display those before
        default to the django default
        '''
        attributes = ['name', 'title', 'slug']
        name = None
        for a in attributes:
            if hasattr(self, a):
                name = getattr(self, a)
        if not name:
            name = repr(self.__class__)
        return name

    def __repr__(self):
        return '<%s[%s]>' % (self.__class__.__name__, self.pk)

    class Meta:
        abstract = True


class OpenGraphShare(BaseModel):
    '''
    Object for tracking all shares to Facebook
    Used for statistics and evaluating how things are going

    I recommend running this in a task
    Example usage:
        from user.models import OpenGraphShare
        user = UserObject
        url = 'http://www.fashiolista.com/'
        kwargs = dict(list=url)

        share = OpenGraphShare.objects.create(
            user = user,
            action_domain='fashiolista:create',
            content_object=self,
        )
        share.set_share_dict(kwargs)
        share.save()
        result = share.send()

    Advanced usage:
        share.send()
        share.update(message='Hello world')
        share.remove()
        share.retry()

    Using this model has the advantage that it allows us to
    - remove open graph shares (since we store the Facebook id)
    - retry open graph shares, which is handy in case of
      - updated access tokens (retry all shares from this user in the last
        facebook_settings.FACEBOOK_OG_SHARE_RETRY_DAYS)
      - Facebook outages (Facebook often has minor interruptions, retry in 15m,
        for max facebook_settings.FACEBOOK_OG_SHARE_RETRIES)
    '''
    objects = model_managers.OpenGraphShareManager()

    user = models.ForeignKey(get_user_model())

    #domain stores
    action_domain = models.CharField(max_length=255)
    facebook_user_id = models.BigIntegerField()

    #what we are sharing, dict and object
    share_dict = models.TextField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    #completion data
    error_message = models.TextField(blank=True, null=True)
    last_attempt = models.DateTimeField(
        blank=True, null=True, auto_now_add=True)
    retry_count = models.IntegerField(blank=True, null=True)
    #only written if we actually succeed
    share_id = models.CharField(blank=True, null=True, max_length=255)
    completed_at = models.DateTimeField(blank=True, null=True)
    #tracking removals
    removed_at = models.DateTimeField(blank=True, null=True)

    #updated at and created at, last one needs an index
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = facebook_settings.FACEBOOK_OG_SHARE_DB_TABLE

    def save(self, *args, **kwargs):
        if self.user and not self.facebook_user_id:
            self.facebook_user_id = self.user.get_profile().facebook_id
        return BaseModel.save(self, *args, **kwargs)

    def send(self, graph=None):
        result = None
        #update the last attempt
        self.last_attempt = datetime.now()
        self.save()

        #see if the graph is enabled
        profile = self.user.get_profile()
        graph = graph or profile.get_offline_graph()
        user_enabled = profile.facebook_open_graph and self.facebook_user_id

        #start sharing
        if graph and user_enabled:
            graph_location = '%s/%s' % (
                self.facebook_user_id, self.action_domain)
            share_dict = self.get_share_dict()
            from open_facebook.exceptions import OpenFacebookException
            try:
                result = graph.set(graph_location, **share_dict)
                share_id = result.get('id')
                if not share_id:
                    error_message = 'No id in Facebook response, found %s for url %s with data %s' % (result, graph_location, share_dict)
                    logger.error(error_message)
                    raise OpenFacebookException(error_message)
                self.share_id = share_id
                self.error_message = None
                self.completed_at = datetime.now()
                self.save()
            except OpenFacebookException, e:
                logger.warn(
                    'Open graph share failed, writing message %s' % e.message)
                self.error_message = unicode(e)
                self.save()
        elif not graph:
            self.error_message = 'no graph available'
            self.save()
        elif not user_enabled:
            self.error_message = 'user not enabled'
            self.save()

        return result

    def update(self, data, graph=None):
        '''
        Update the share with the given data
        '''
        result = None
        profile = self.user.get_profile()
        graph = graph or profile.get_offline_graph()

        #update the share dict so a retry will do the right thing
        #just in case we fail the first time
        shared = self.update_share_dict(data)
        self.save()

        #broadcast the change to facebook
        if self.share_id:
            result = graph.set(self.share_id, **shared)

        return result

    def remove(self, graph=None):
        if not self.share_id:
            raise ValueError('Can only delete shares which have an id')
        #see if the graph is enabled
        profile = self.user.get_profile()
        graph = graph or profile.get_offline_graph()
        response = None
        if graph:
            response = graph.delete(self.share_id)
            self.removed_at = datetime.now()
            self.save()
        return response

    def retry(self, graph=None, reset_retries=False):
        if self.completed_at:
            raise ValueError('You can\'t retry completed shares')

        if reset_retries:
            self.retry_count = 0
        #handle the case where self.retry_count = None
        self.retry_count = self.retry_count + 1 if self.retry_count else 1

        #actually retry now
        result = self.send(graph=graph)
        return result

    def set_share_dict(self, share_dict):
        share_dict_string = json.dumps(share_dict)
        self.share_dict = share_dict_string

    def get_share_dict(self):
        share_dict_string = self.share_dict
        share_dict = json.loads(share_dict_string)
        return share_dict

    def update_share_dict(self, share_dict):
        old_share_dict = self.get_share_dict()
        old_share_dict.update(share_dict)
        self.set_share_dict(old_share_dict)
        return old_share_dict


class FacebookInvite(CreatedAtAbstractBase):
    user = models.ForeignKey(get_user_model())
    user_invited = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    type = models.CharField(blank=True, null=True, max_length=255)

    #status data
    wallpost_id = models.CharField(blank=True, null=True, max_length=255)
    error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    last_attempt = models.DateTimeField(
        blank=True, null=True, auto_now_add=True)

    #reminder data
    reminder_wallpost_id = models.CharField(
        blank=True, null=True, max_length=255)
    reminder_error = models.BooleanField(default=False)
    reminder_error_message = models.TextField(blank=True, null=True)
    reminder_last_attempt = models.DateTimeField(
        blank=True, null=True, auto_now_add=True)

    def __unicode__(self):
        message = 'user %s invited fb id %s' % (self.user, self.user_invited)
        return message

    def resend(self, graph=None):
        from django_facebook.invite import post_on_profile
        if not graph:
            graph = self.user.get_profile().get_offline_graph()
            if not graph:
                return
        facebook_id = self.user_invited
        invite_result = post_on_profile(
            self.user, graph, facebook_id, self.message, force_send=True)
        return invite_result

    class Meta:
        unique_together = ('user', 'user_invited')

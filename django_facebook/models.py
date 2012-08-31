from django_facebook import settings as facebook_settings
from django.core.urlresolvers import reverse
from django_facebook import model_managers
from django.conf import settings
from django.db import models
import os
import datetime
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
import logging
from open_facebook.utils import json, camel_to_underscore
from django.db.models.base import ModelBase
import sys
logger = logging.getLogger(__name__)


PROFILE_IMAGE_PATH = os.path.join('images', 'facebook_profiles/%Y/%m/%d')




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
    gender = models.CharField(max_length=1, choices=(('m', 'Male'), ('f', 'Female')), blank=True, null=True)
    raw_data = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.user.__unicode__()

    class Meta:
        abstract = True

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
                                 next_key='register_next')
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
        access_token, expires = results['access_token'], results['expires']
        self.access_token = access_token
        self.save()
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
    gender = models.CharField(choices=(('F', 'female'), ('M', 'male')), blank=True, null=True, max_length=1)

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
    user = models.OneToOneField('auth.User')


if settings.AUTH_PROFILE_MODULE == 'django_facebook.FacebookProfile':
    '''
    If we are using the django facebook profile model, create the model
    and connect it to the user create signal
    '''

    from django.contrib.auth.models import User
    from django.db.models.signals import post_save

    #Make sure we create a FacebookProfile when creating a User
    def create_facebook_profile(sender, instance, created, **kwargs):
        if created:
            FacebookProfile.objects.create(user=instance)

    post_save.connect(create_facebook_profile, sender=User)


class BaseModelMetaclass(ModelBase):
    '''
    Cleaning up the table naming conventions
    '''

    def __new__(cls, name, bases, attrs):
        super_new = ModelBase.__new__(cls, name, bases, attrs)
        module_name = camel_to_underscore(name)
        model_module = sys.modules[cls.__module__]

        app_label = super_new.__module__.split('.')[-2]
        db_table = '%s_%s' % (app_label, module_name)
        if not getattr(super_new._meta, 'proxy', False):
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


class OpenGraphShare(CreatedAtAbstractBase):
    '''
    Object for tracking all shares to facebook
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
    '''
    from django.contrib.auth.models import User
    user = models.ForeignKey(User)

    #domain stores
    action_domain = models.CharField(max_length=255)
    facebook_user_id = models.BigIntegerField()

    #what we are sharing, dict and object
    share_dict = models.TextField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    #completion data
    completed_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    last_attempt = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    share_id = models.CharField(blank=True, null=True, max_length=255)

    def save(self, *args, **kwargs):
        if self.user and not self.facebook_user_id:
            self.facebook_user_id = self.user.get_profile().facebook_id
        return models.Model.save(self, *args, **kwargs)

    def send(self):
        result = None
        #update the last attempt
        self.last_attempt = datetime.datetime.now()
        self.save()

        #see if the graph is enabled
        profile = self.user.get_profile()
        graph = profile.get_offline_graph()
        user_enabled = profile.facebook_open_graph and self.facebook_user_id

        #start sharing
        if graph and user_enabled:
            graph_location = '%s/%s' % (self.facebook_user_id, self.action_domain)
            share_dict = self.get_share_dict()
            from open_facebook.exceptions import OpenFacebookException
            try:
                result = graph.set(graph_location, **share_dict)
                share_id = result.get('id')
                if not share_id:
                    error_message = 'No id in facebook response, found %s for url %s with data %s' % (result, graph_location, share_dict)
                    logger.error(error_message)
                    raise OpenFacebookException(error_message)
                self.share_id = share_id
                self.error_message = None
                self.completed_at = datetime.datetime.now()
                self.save()
            except OpenFacebookException, e:
                self.error_message = unicode(e)
                self.save()
        elif not graph:
            self.error_message = 'no graph available'
            self.save()
        elif not user_enabled:
            self.error_message = 'user not enabled'
            self.save()

        return result

    def set_share_dict(self, share_dict):
        share_dict_string = json.encode(share_dict)
        self.share_dict = share_dict_string
    
    def get_share_dict(self):
        share_dict_string = self.share_dict
        share_dict = json.decode(share_dict_string)
        return share_dict
    
    
class FacebookInvite(CreatedAtAbstractBase):
    from django.contrib.auth.models import User
    user = models.ForeignKey(User)
    user_invited = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    type = models.CharField(blank=True, null=True, max_length=255)

    #status data
    wallpost_id = models.CharField(blank=True, null=True, max_length=255)
    error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    last_attempt = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    
    #reminder data
    reminder_wallpost_id = models.CharField(blank=True, null=True, max_length=255)
    reminder_error = models.BooleanField(default=False)
    reminder_error_message = models.TextField(blank=True, null=True)
    reminder_last_attempt = models.DateTimeField(blank=True, null=True, auto_now_add=True)

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
        invite_result = post_on_profile(self.user, graph, facebook_id, self.message, force_send=True)
        return invite_result
    
    class Meta:
        unique_together = ('user', 'user_invited')
    


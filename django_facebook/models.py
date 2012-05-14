from django.db import models
from django.core.urlresolvers import reverse
from django_facebook import model_managers
from django.conf import settings
import os





PROFILE_IMAGE_PATH = os.path.join('images','facebook_profiles/%Y/%m/%d')


class FacebookProfileModel(models.Model):
    '''
    Abstract class to add to your profile model.
    NOTE: If you don't use this this abstract class, make sure you copy/paste
    the fields in.
    '''
    about_me = models.TextField(blank=True)
    facebook_id = models.BigIntegerField(blank=True, unique=True, null=True)
    access_token = models.TextField(
        blank=True, help_text='Facebook token for offline access')
    facebook_name = models.CharField(max_length=255, blank=True)
    facebook_profile_url = models.TextField(blank=True)
    website_url = models.TextField(blank=True)
    blog_url = models.TextField(blank=True)
    image = models.ImageField(blank=True, null=True,
        upload_to=PROFILE_IMAGE_PATH, max_length=255)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=(('m', 'Male'), ('f', 'Female')), blank=True, null=True)
    raw_data = models.TextField(blank=True)

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
    
    def clear_access_token(self):
        self.access_token = None
        self.save()

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
        



class FacebookUser(models.Model):
    '''
    Model for storing a users friends
    '''
    # in order to be able to easily move these to an another db,
    # use a user_id and no foreign key
    user_id = models.IntegerField()
    facebook_id = models.BigIntegerField()
    name = models.TextField(blank=True, null=True)
    gender = models.CharField(choices=(('F', 'female'),('M', 'male')), blank=True, null=True, max_length=1)

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
        
        
if settings.AUTH_PROFILE_MODULE == 'django_facebook.FacebookProfile':
    '''
    If we are using the django facebook profile model, create the model
    and connect it to the user create signal
    '''
        
    class FacebookProfile(FacebookProfileModel):
        '''
        Not abstract version of the facebook profile model
        Use this by setting
        AUTH_PROFILE_MODULE = 'django_facebook.FacebookProfile' 
        '''
        user = models.OneToOneField('auth.User')
    
    from django.contrib.auth.models import User
    from django.db.models.signals import post_save
    
    #Make sure we create a FacebookProfile when creating a User
    def create_facebook_profile(sender, instance, created, **kwargs):
        if created:
            FacebookProfile.objects.create(user=instance)
    
    post_save.connect(create_facebook_profile, sender=User)
        

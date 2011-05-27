from django.db import models
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

class FacebookProfileModel(models.Model):
    '''
    Abstract class to add to your profile model.
    
    NOTE: If you don't use this this abstract class, make sure you copy/paste
    the fields in.
    '''
    about_me = models.TextField(blank=True, null=True)
    facebook_id = models.BigIntegerField(blank=True, null=True, unique=True)
    facebook_name = models.CharField(max_length=255, blank=True, null=True)
    facebook_profile_url = models.TextField(blank=True, null=True)
    website_url = models.TextField(blank=True, null=True)
    blog_url = models.TextField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True,
        upload_to='profile_images', max_length=255)
    date_of_birth = models.DateField(blank=True, null=True)
    raw_data = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.user.__unicode__()
    
    class Meta:
        abstract = True
        
    def post_facebook_registration(self, request):
        '''
        Behaviour after registering with facebook
        '''
        from django_facebook.utils import next_redirect
        default_url = reverse('facebook_connect')
        response = next_redirect(request, default=default_url, next_key='register_next')
        response.set_cookie('fresh_registration', self.user_id)
        
        return response


        

class FacebookUser(models.Model):
    '''
    Model for storing a users friends
    '''
    user = models.ForeignKey('auth.User')
    facebook_id = models.BigIntegerField()
    name = models.TextField()

    class Meta:
        unique_together = ['user', 'facebook_id']

class FacebookLike(models.Model):
    '''
    Model for storing all of a users fb likes
    '''
    user = models.ForeignKey('auth.User')
    facebook_id = models.BigIntegerField()
    name = models.TextField()
    category = models.TextField(blank=True, null=True)
    created_time = models.DateTimeField()
    
    class Meta:
        unique_together = ['user', 'facebook_id']
        
        
        
        
from django.db import models
from django_facebook import settings as facebook_settings


class FacebookProfileModel(models.Model):
    '''
    Abstract class to add to your profile model.
    
    NOTE: If you don't use this this abstract class, make sure you copy/paste
    the fields in.
    '''
    about_me = models.TextField(blank=True, null=True)
    facebook_id = models.IntegerField(blank=True, null=True)
    facebook_name = models.CharField(max_length=255, blank=True, null=True)
    facebook_profile_url = models.TextField(blank=True, null=True)
    website_url = models.TextField(blank=True, null=True)
    blog_url = models.TextField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True, upload_to='profile_images')
    date_of_birth = models.DateField(blank=True, null=True)
    if facebook_settings.FACEBOOK_TRACK_RAW_DATA:
        raw_data = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.user.__unicode__()
    
    class Meta:
        abstract = True
        

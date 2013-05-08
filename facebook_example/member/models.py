from django.db import models
from django_facebook.models import FacebookModel
from django_facebook.models import get_user_model
from django.conf import settings
from django_facebook.utils import try_get_profile, get_profile_model

try:
    from django.contrib.auth.models import AbstractUser, UserManager
    class FacebookUser(AbstractUser, FacebookModel):
        '''
        The django 1.5 approach to adding the facebook related fields
        '''
        objects = UserManager()
except ImportError, e:
    pass




# Create your models here.
class UserProfile(FacebookModel):
    '''
    Inherit the properties from django facebook
    '''
    user = models.OneToOneField(settings.AUTH_USER_MODEL)


from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save)
def create_profile(sender, instance, created, **kwargs):
    """Create a matching profile whenever a user object is created."""
    if sender == get_user_model():
        user = instance
        profile_model = get_profile_model()
        if profile_model == UserProfile and created:
            profile, new = UserProfile.objects.get_or_create(user=instance)

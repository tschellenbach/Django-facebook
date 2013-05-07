from django.db import models
from django_facebook.models import FacebookModel
from django_facebook.models import get_user_model
from django.conf import settings

try:
    from django.contrib.auth.models import AbstractUser, UserManager
    parents = (AbstractUser, FacebookModel)
except ImportError, e:
    AbstractUser = None
    parents = (object,)

if AbstractUser:
    class FacebookUser(AbstractUser, FacebookModel):
        '''
        The django 1.5 approach to adding the facebook related fields
        '''
        objects = UserManager()


# Create your models here.
class UserProfile(FacebookModel):
    '''
    Inherit the properties from django facebook
    '''
    user = models.OneToOneField(settings.AUTH_USER_MODEL)


from django.db.models.signals import post_save
from django.dispatch import receiver


#@receiver(post_save, sender=get_user_model())
#def create_profile(sender, instance, created, **kwargs):
#    """Create a matching profile whenever a user object is created."""
#    if created:
#        profile, new = UserProfile.objects.get_or_create(user=instance)

from django.db import models
from django_facebook.models import FacebookProfileModel
from django_facebook.models import get_user_model


# Create your models here.
class UserProfile(FacebookProfileModel):
    '''
    Inherit the properties from django facebook
    '''
    user = models.OneToOneField(get_user_model())


from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=get_user_model())
def create_profile(sender, instance, created, **kwargs):
    """Create a matching profile whenever a user object is created."""
    if created:
        profile, new = UserProfile.objects.get_or_create(user=instance)

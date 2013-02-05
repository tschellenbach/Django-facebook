from django.conf.urls.defaults import patterns, url
from django_facebook import settings as facebook_settings

urlpatterns = patterns('django_facebook.views',
                       url(r'^connect/$', 'connect', name='facebook_connect'),
                       url(r'^disconnect/$',
                           'disconnect', name='facebook_disconnect'),
                       url(r'^image_upload/$',
                           'image_upload', name='facebook_image_upload'),
                       url(r'^wall_post/$',
                           'wall_post', name='facebook_wall_post'),
                       url(r'^canvas/$', 'canvas', name='facebook_canvas'),
                       )


#help autodiscovery a bit
from django_facebook import admin

# putting this here instead of models.py reduces issues with import ordering
from django.conf import settings


if settings.AUTH_PROFILE_MODULE == 'django_facebook.FacebookProfile':
    '''
    If we are using the django facebook profile model, create the model
    and connect it to the user create signal
    '''

    from django.db.models.signals import post_save
    from django_facebook.models import FacebookProfile
    from django_facebook.utils import get_user_model

    #Make sure we create a FacebookProfile when creating a User
    def create_facebook_profile(sender, instance, created, **kwargs):
        if created:
            FacebookProfile.objects.create(user=instance)

    post_save.connect(create_facebook_profile, sender=get_user_model())

from django.conf.urls.defaults import patterns, url, include


urlpatterns = patterns('django_facebook.views',
   url(r'^connect/$', 'connect', name='facebook_connect'),
)


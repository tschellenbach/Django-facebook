from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('django_facebook.views',
   url(r'^connect/$', 'connect', name='facebook_connect'),
   url(r'^image_upload/$', 'image_upload', name='facebook_image_upload'),
   url(r'^wall_post/$', 'wall_post', name='facebook_wall_post'),
   url(r'^canvas/$', 'canvas', name='facebook_canvas'),
   url(r'^page_tab/$', 'page_tab', name='facebook_page_tab'),
)


#help autodiscovery a bit
from django_facebook import admin

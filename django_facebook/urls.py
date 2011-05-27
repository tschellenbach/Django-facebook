from django.conf.urls.defaults import patterns, url, include


urlpatterns = patterns('django_facebook.views',
   url(r'^connect/$', 'connect', name='facebook_connect'),
)

#examples to connect the canvas views
#url(r'^canvas/$', 'canvas', name='facebook_canvas'),
#url(r'^canvas/my_style/$', 'my_style', name='facebook_my_style'),

#TODO: figure out why autodiscover doenst seem to detect the admin
from django_facebook import admin
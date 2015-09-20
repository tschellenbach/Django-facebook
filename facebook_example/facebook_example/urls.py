from member.views import timestamp_visit_view, home_view

try:
    from django.conf.urls import include, patterns, url
except ImportError:
    from django.conf.urls.defaults import include, patterns, url
from django.conf import settings
# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
                       # facebook and registration urls
                       (r'^facebook/', include('django_facebook.urls')),
                       (r'^accounts/', include('django_facebook.auth_urls')),
                       (r'^timestamp_visit$', timestamp_visit_view),
                       (r'^$', home_view)
)

if settings.MODE == 'userena':
    urlpatterns += patterns('',
                            (r'^accounts/', include('userena.urls')),
    )
elif settings.MODE == 'django_registration':
    urlpatterns += patterns('',
                            (r'^accounts/', include(
                                'registration.backends.default.urls')),
    )

if settings.DEBUG:
    urlpatterns += patterns('',
                            url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
                                'document_root': settings.MEDIA_ROOT,
                            }),
    )

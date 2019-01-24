try:
    from django.conf.urls import include, url
except ImportError:
    from django.conf.urls.defaults import include, url
from django.conf import settings
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    # facebook and registration urls
    url(r'^facebook/', include('django_facebook.urls')),
    url(r'^accounts/', include('django_facebook.auth_urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
]

if settings.MODE == 'userena':
    urlpatterns += [
        url(r'^accounts/', include('userena.urls')),
    ]
elif settings.MODE == 'django_registration':
    urlpatterns += [
        url(r'^accounts/', include('registration.backends.default.urls')),
    ]


if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            }),
        ]

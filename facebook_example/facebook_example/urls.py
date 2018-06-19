from django.conf.urls import include, url
from django.urls import path
from django.conf import settings
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    # facebook and registration urls
    url(r'^facebook/', include('django_facebook.urls')),
    url(r'^accounts/', include('django_facebook.auth_urls')),
    path('admin/', admin.site.urls),
]

if settings.MODE == 'userena':
    urlpatterns += [
        url(r'^accounts/', include('userena.urls')),
    ]
elif settings.MODE == 'django_registration':
    urlpatterns += [
        url(r'^accounts/', include('registration.backends.default.urls')),
    ]

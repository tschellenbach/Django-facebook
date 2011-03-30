
from django.conf import settings
from django.middleware.csrf import get_token
from django.utils.functional import lazy


def facebook(request):
    """
    Context processor that provides a CSRF token, or the string 'NOTPROVIDED' if
    it has not been provided by either a view decorator or the middleware
    """
    context = {}
    from django_facebook import settings as facebook_settings
    context['FACEBOOK_API_KEY'] = facebook_settings.FACEBOOK_API_KEY
    context['FACEBOOK_APP_ID'] = facebook_settings.FACEBOOK_APP_ID
    
    return context



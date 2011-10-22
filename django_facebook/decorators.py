from django.contrib.auth import REDIRECT_FIELD_NAME
from django_facebook import settings as facebook_settings
from django.http import QueryDict
from django.contrib.auth.decorators import user_passes_test
from django_facebook.utils import parse_scope



def connect_required():
    pass



def facebook_required(function=None, scope=facebook_settings.FACEBOOK_DEFAULT_SCOPE, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator which makes the view require the given Facebook perms, redirecting
    to the log-in page if necessary.
    
    Note we don't actually query the permissions, we just try in the view
    and upon a permission error redirect to login_url
    Querying the permissions would slow down things
    """
    from django.conf import settings
    scope = parse_scope(scope)
    login_url = login_url or settings.LOGIN_URL
    query_dict = QueryDict('', True)
    query_dict['scope'] = ','.join(scope)
    login_url = '%s?%s' % (login_url, query_dict.urlencode())
    
    actual_decorator = user_passes_test(
        lambda u: True,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
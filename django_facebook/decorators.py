from django.contrib.auth import REDIRECT_FIELD_NAME
from django_facebook import settings as facebook_settings
from django.http import HttpResponseRedirect
from django_facebook.utils import get_oauth_url, parse_scope
from django.utils.decorators import available_attrs
from django.utils.functional import wraps
from open_facebook import exceptions as facebook_exceptions

import logging
logger = logging.getLogger(__name__)


def facebook_required(view_func=None, scope=facebook_settings.FACEBOOK_DEFAULT_SCOPE, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator which makes the view require the given Facebook perms, redirecting
    to the log-in page if necessary.
    
    Note we don't actually query the permissions, we just try in the view
    and upon a permission error redirect to login_url
    Querying the permissions would slow down things
    """
    scope_list = parse_scope(scope)
    def test_permissions(request, redirect_uri=None):
        '''
        Call Facebook me/permissions to see if we are allowed to do this
        '''
        from django_facebook.api import get_persistent_graph
        fb = get_persistent_graph(request, redirect_uri=redirect_uri)
        permissions_dict = {}
        
        if fb:
            try:
                permissions_response = fb.get('me/permissions')
                permissions = permissions_response['data'][0]
            except facebook_exceptions.OAuthException, e:
                #this happens when someone revokes their permissions while the session
                #is still stored
                permissions = {}
            permissions_dict = dict([(k,bool(int(v))) for k,v in permissions.items() if v == '1' or v == 1])
            
        #see if we have all permissions
        scope_allowed = True
        for permission in scope_list:
            if permission not in permissions_dict:
                scope_allowed = False
                
        #raise if this happens after a redirect though
        if not scope_allowed and request.GET.get('attempt'):
            raise ValueError, 'Somehow facebook is not giving us the permissions needed, lets break instead of endless redirects. Fb was %s and permissions %s' % (fb, permissions_dict)

        return scope_allowed
            
    def actual_decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            oauth_url, redirect_uri = get_oauth_url(request, scope_list)
            if test_permissions(request, redirect_uri):
                return view_func(request, *args, **kwargs)
            else:
                logger.info('requesting access with redirect uri: %s', redirect_uri)
                response = HttpResponseRedirect(oauth_url)
                return response
        return _wrapped_view
    
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator



def facebook_connect_required():
    """
    Makes sure that the user is registered within your application (using facebook)
    Before going on to the next page
    """
    #TODO: BUILD THIS :)
    pass


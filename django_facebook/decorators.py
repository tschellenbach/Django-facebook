from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.decorators import available_attrs
from django.utils.functional import wraps
from django_facebook import settings as fb_settings
from django_facebook import get_persistent_graph
from django_facebook.utils import get_oauth_url, parse_scope, response_redirect
import logging
from django_facebook.api import require_persistent_graph
from open_facebook import exceptions as open_facebook_exceptions


logger = logging.getLogger(__name__)


def facebook_required(view_func=None, scope=None, canvas=False):
    """
    Decorator which makes the view require the given Facebook perms,
    redirecting to the log-in page if necessary.

    Note we don't actually query the permissions, we just try in the view
    and upon a permission error redirect to login_url
    Querying the permissions would slow down things
    """
    from open_facebook import exceptions as open_facebook_exceptions
    scope = fb_settings.FACEBOOK_DEFAULT_SCOPE if scope is None else scope
    scope_list = parse_scope(scope)
    # canvas pages always need to be csrf excempt
    csrf_exempt = canvas

    def actual_decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            oauth_url, current_uri, redirect_uri = get_oauth_url(
                request, scope_list)
            graph = get_persistent_graph(request, redirect_uri=redirect_uri)

            # Normal Facebook errors should be raised
            # OAuthException s should cause a redirect for authorization
            from django_facebook.utils import has_permissions
            permissions_granted = has_permissions(graph, scope_list)
            
            def normal_view(*args, **kwargs):
                try:
                    result = view_func(*args, **kwargs)
                except TypeError, e:
                    result = view_func(*args, **kwargs)
                return result
                
            if permissions_granted:
                return normal_view(request, graph=graph, *args, **kwargs)
            elif request.REQUEST.get('attempt') == '1':
                # Doing a redirect could end up causing infinite redirects
                # If Facebook is somehow not giving permissions
                # Time to show an error page
                msg = '''\
                    Somehow Facebook is not giving us the permissions needed
                    Lets cancel instead of endless redirects
                '''
                logger.info(msg)
                return normal_view(request, graph=None, *args, **kwargs)
            else:
                logger.info('requesting access with redirect URI: %s',
                            redirect_uri)
                response = response_redirect(oauth_url, canvas=canvas)
                return response
        return _wrapped_view

    if view_func:
        wrapped_view = actual_decorator(view_func)
    else:
        wrapped_view = actual_decorator

    if csrf_exempt:
        # always set canvas pages to be csrf exempt
        wrapped_view.csrf_exempt = csrf_exempt

    return wrapped_view


def facebook_required_lazy(view_func=None, scope=None, extra_params=None, canvas=False):
    """
    Decorator which makes the view require the given Facebook perms,
    redirecting to the log-in page if necessary.
    Based on exceptions instead of a check up front
    Faster, but more prone to bugs

    Use this in combination with require_persistent_graph
    """
    scope = fb_settings.FACEBOOK_DEFAULT_SCOPE if scope is None else scope
    scope_list = parse_scope(scope)
    # canvas pages always need to be csrf excempt
    csrf_exempt = canvas

    def actual_decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            oauth_url, current_uri, redirect_uri = get_oauth_url(
                request, scope_list,
                extra_params=extra_params)
            from django_facebook.utils import has_permissions
            graph = None
            
            def normal_view(*args, **kwargs):
                try:
                    result = view_func(*args, **kwargs)
                except TypeError, e:
                    result = view_func(*args, **kwargs)
                return result
            
            try:
                # call get persistent graph and convert the
                # token with correct redirect uri
                graph = require_persistent_graph(request, redirect_uri=current_uri)
                # Note we're not requiring a persistent graph here
                # You should require a persistent graph in the view when you start using this
                return normal_view(request, graph=graph, *args, **kwargs)
            except open_facebook_exceptions.OpenFacebookException, e:
                permission_granted = has_permissions(graph, scope_list)
                if permission_granted:
                    # an error if we already have permissions
                    # shouldn't have been caught
                    # raise to prevent bugs with error mapping to cause issues
                    raise
                elif request.REQUEST.get('attempt') == '1':
                    # Doing a redirect could end up causing infinite redirects
                    # If Facebook is somehow not giving permissions
                    # Time to show an error page
                    msg = '''\
                        Somehow Facebook is not giving us the permissions needed
                        Lets cancel instead of endless redirects
                    '''
                    logger.info(msg)
                    return normal_view(request, graph=None, *args, **kwargs)
                else:
                    logger.info(
                        u'requesting access with redirect uri: %s, error was %s',
                        redirect_uri, e)
                    response = response_redirect(oauth_url, canvas=canvas)
                    return response
        return _wrapped_view

    if view_func:
        wrapped_view = actual_decorator(view_func)
    else:
        wrapped_view = actual_decorator

    if csrf_exempt:
        # always set canvas pages to be csrf exempt
        wrapped_view.csrf_exempt = csrf_exempt

    return wrapped_view


def facebook_connect_required():
    """
    Makes sure that the user is registered within your
    application (using facebook) before going on to the next page
    """
    # TODO: BUILD THIS :)
    pass

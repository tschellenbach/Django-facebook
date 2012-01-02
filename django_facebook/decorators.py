from django.contrib.auth import REDIRECT_FIELD_NAME
from django_facebook import settings as fb_settings
from django.http import HttpResponseRedirect
from django_facebook.utils import get_oauth_url, parse_scope, response_redirect
from django.utils.decorators import available_attrs
from django.utils.functional import wraps

import logging
from django_facebook.api import get_persistent_graph
logger = logging.getLogger(__name__)


def facebook_required(view_func=None, scope=fb_settings.FACEBOOK_DEFAULT_SCOPE,
                      redirect_field_name=REDIRECT_FIELD_NAME, login_url=None, canvas=False):
    """
    Decorator which makes the view require the given Facebook perms,
    redirecting to the log-in page if necessary.

    Note we don't actually query the permissions, we just try in the view
    and upon a permission error redirect to login_url
    Querying the permissions would slow down things
    """
    from django_facebook.utils import test_permissions
    scope_list = parse_scope(scope)

    def actual_decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            oauth_url, redirect_uri = get_oauth_url(request, scope_list)
            if test_permissions(request, scope_list, redirect_uri):
                return view_func(request, *args, **kwargs)
            else:
                logger.info('requesting access with redirect uri: %s',
                            redirect_uri)
                response = response_redirect(oauth_url, canvas=canvas)
                return response
        return _wrapped_view

    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def facebook_required_lazy(view_func=None,
                           scope=fb_settings.FACEBOOK_DEFAULT_SCOPE,
                           redirect_field_name=REDIRECT_FIELD_NAME,
                           login_url=None, extra_params=None, canvas=False):
    """
    Decorator which makes the view require the given Facebook perms,
    redirecting to the log-in page if necessary.
    Based on exceptions instead of a check up front
    Faster, but more prone to bugs
    """
    from django_facebook.utils import test_permissions
    from open_facebook import exceptions as open_facebook_exceptions
    scope_list = parse_scope(scope)

    def actual_decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            oauth_url, redirect_uri = get_oauth_url(request, scope_list,
                                                    extra_params=extra_params)
            try:
                # call get persistent graph and convert the
                # token with correct redirect uri
                get_persistent_graph(request, redirect_uri=redirect_uri)
                return view_func(request, *args, **kwargs)
            except open_facebook_exceptions.OpenFacebookException, e:
                if test_permissions(request, scope_list, redirect_uri):
                    # an error if we already have permissions
                    # shouldn't have been caught
                    # raise to prevent bugs with error mapping to cause issues
                    raise
                else:
                    logger.info(u'requesting access with redirect uri: %s, error was %s',
                                redirect_uri, e)
                    response = response_redirect(oauth_url, canvas=canvas)
                    return response
        return _wrapped_view

    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def facebook_connect_required():
    """
    Makes sure that the user is registered within your
    application (using facebook)bBefore going on to the next page
    """
    #TODO: BUILD THIS :)
    pass

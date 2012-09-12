from django.contrib.auth import REDIRECT_FIELD_NAME
from django_facebook import settings as fb_settings

from django.http import HttpResponseRedirect
from django_facebook.utils import get_oauth_url, parse_scope, response_redirect
from django.utils.decorators import available_attrs
from django.utils.functional import wraps

import logging
from django_facebook.api import require_persistent_graph, get_persistent_graph
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
    from open_facebook import exceptions as open_facebook_exceptions
    from django_facebook.utils import test_permissions
    scope_list = parse_scope(scope)
    #canvas pages always need to be csrf excempt
    csrf_exempt = canvas

    def actual_decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            oauth_url, current_uri, redirect_uri = get_oauth_url(
                request, scope_list)

            #Normal facebook errors should be raised
            #OAuthException s should cause a redirect for authorization
            try:
                permission_granted = test_permissions(
                    request, scope_list, current_uri)
            except open_facebook_exceptions.OAuthException, e:
                permission_granted = False

            if permission_granted:
                return view_func(request, *args, **kwargs)
            else:
                logger.info('requesting access with redirect uri: %s',
                            redirect_uri)
                response = response_redirect(oauth_url, canvas=canvas)
                return response
        return _wrapped_view

    if view_func:
        wrapped_view = actual_decorator(view_func)
    else:
        wrapped_view = actual_decorator

    if csrf_exempt:
        #always set canvas pages to be csrf exempt
        wrapped_view.csrf_exempt = csrf_exempt

    return wrapped_view


def facebook_required_lazy(view_func=None,
                           scope=fb_settings.FACEBOOK_DEFAULT_SCOPE,
                           redirect_field_name=REDIRECT_FIELD_NAME,
                           login_url=None, extra_params=None, canvas=False):
    """
    Decorator which makes the view require the given Facebook perms,
    redirecting to the log-in page if necessary.
    Based on exceptions instead of a check up front
    Faster, but more prone to bugs

    Use this in combination with require_persistent_graph
    """
    from django_facebook.utils import test_permissions
    from open_facebook import exceptions as open_facebook_exceptions
    scope_list = parse_scope(scope)
    #canvas pages always need to be csrf excempt
    csrf_exempt = canvas

    def actual_decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            oauth_url, current_uri, redirect_uri = get_oauth_url(
                request, scope_list,
                extra_params=extra_params)
            try:
                # call get persistent graph and convert the
                # token with correct redirect uri
                get_persistent_graph(request, redirect_uri=current_uri)
                #Note we're not requiring a persistent graph here
                #You should require a persistent graph in the view when you start using this
                return view_func(request, *args, **kwargs)
            except open_facebook_exceptions.OpenFacebookException, e:
                permission_granted = test_permissions(
                    request, scope_list, current_uri)
                if permission_granted:
                    # an error if we already have permissions
                    # shouldn't have been caught
                    # raise to prevent bugs with error mapping to cause issues
                    raise
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
        #always set canvas pages to be csrf exempt
        wrapped_view.csrf_exempt = csrf_exempt

    return wrapped_view


def facebook_connect_required():
    """
    Makes sure that the user is registered within your
    application (using facebook)bBefore going on to the next page
    """
    #TODO: BUILD THIS :)
    pass

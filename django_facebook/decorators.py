from django.utils.decorators import available_attrs
from django.utils.functional import wraps
from django_facebook import settings as fb_settings
from django_facebook.api import get_persistent_graph, require_persistent_graph
from django_facebook.utils import get_oauth_url, parse_scope, response_redirect, \
    has_permissions, simplify_class_decorator
from open_facebook import exceptions as open_facebook_exceptions
import logging


logger = logging.getLogger(__name__)


class FacebookRequired(object):

    """
    Decorator which makes the view require the given Facebook perms,
    redirecting to the log-in page if necessary.

    Note we don't actually query the permissions, we just try in the view
    and upon a permission error redirect to login_url
    Querying the permissions would slow down things
    """

    def __init__(self, fn, scope=None, canvas=False, page_tab=False, extra_params=None):
        self.fn = fn
        scope = fb_settings.FACEBOOK_DEFAULT_SCOPE if scope is None else scope
        self.scope = scope
        self.scope_list = parse_scope(scope)
        self.canvas = canvas
        self.page_tab = page_tab
        self.extra_params = extra_params
        # canvas pages always need to be csrf excempt
        csrf_exempt = canvas or page_tab
        self.csrf_exempt = csrf_exempt

    def authenticate(self, fn, request, *args, **kwargs):
        '''
        Authenticate the user

        There are three options
        a.) We have permissions, proceed with the view
        b.) We tried getting permissions and failed, abort...
        c.) We are about to ask for permissions
        '''
        redirect_uri = self.get_redirect_uri(request)
        oauth_url = get_oauth_url(
            self.scope_list, redirect_uri, extra_params=self.extra_params)

        graph = get_persistent_graph(request, redirect_uri=redirect_uri)

        # See if we have all permissions
        permissions_granted = has_permissions(graph, self.scope_list)

        if permissions_granted:
            response = self.execute_view(
                fn, request, graph=graph, *args, **kwargs)
        elif request.REQUEST.get('attempt') == '1':
            # Doing a redirect could end up causing infinite redirects
            # If Facebook is somehow not giving permissions
            # Time to show an error page
            response = self.authentication_failed(fn, request, *args, **kwargs)
        else:
            response = self.oauth_redirect(oauth_url, redirect_uri)

        return response

    def get_redirect_uri(self, request):
        '''
        return the redirect uri to use for oauth authorization
        this needs to be the same for requesting and accepting the token
        '''
        if self.canvas:
            redirect_uri = fb_settings.FACEBOOK_CANVAS_PAGE
        else:
            redirect_uri = request.build_absolute_uri()

        # set attempt=1 to prevent endless redirect loops
        if 'attempt=1' not in redirect_uri:
            if '?' not in redirect_uri:
                redirect_uri += '?attempt=1'
            else:
                redirect_uri += '&attempt=1'

        return redirect_uri

    def __call__(self):
        '''
        When the decorator is called like this
            @facebook_required
            The call will receive

        Otherwise it will be like
            @facebook_required(scope=[])
            The init will receive the parameters
        '''
        @wraps(self.fn, assigned=available_attrs(self.fn))
        def wrapped_view(request, *args, **kwargs):
            response = self.authenticate(self.fn, request, *args, **kwargs)
            return response

        wrapped_view.csrf_exempt = self.csrf_exempt
        return wrapped_view

    def oauth_redirect(self, oauth_url, redirect_uri, e=None):
        '''
        Redirect to Facebook's oAuth dialog
        '''
        logger.info(
            u'requesting access with redirect uri: %s, error was %s',
            redirect_uri, e)

        # for internal Facebook pages we should use a script to redirect
        script_redirect = False
        if self.canvas or self.page_tab:
            script_redirect = True

        # redirect using HTTP headers or a script
        response = response_redirect(
            oauth_url, script_redirect=script_redirect)
        return response

    def authentication_failed(self, fn, request, *args, **kwargs):
        '''
        Execute the view but don't pass the graph to indicate we couldn't
        get the right permissions
        '''
        msg = '''\
            Somehow Facebook is not giving us the permissions needed
            Lets cancel instead of endless redirects
        '''
        logger.info(msg)
        response = self.execute_view(fn, request, graph=None, *args, **kwargs)
        return response

    def execute_view(self, view_func, *args, **kwargs):
        try:
            result = view_func(*args, **kwargs)
        except TypeError, e:
            # this might be another error type error, raise it
            # the only way I know to check this is the message :(
            if 'graph' not in e.message:
                raise
            graph = kwargs.pop('graph', None)
            result = view_func(*args, **kwargs)
        return result


# decorators should look like functions :)
facebook_required = simplify_class_decorator(FacebookRequired)


class FacebookRequiredLazy(FacebookRequired):

    """
    Decorator which makes the view require the given Facebook perms,
    redirecting to the log-in page if necessary.

    Based on exceptions instead of a permission check
    Faster, but more prone to bugs

    Use this in combination with require_persistent_graph
    """

    def authenticate(self, fn, request, *args, **kwargs):
        redirect_uri = self.get_redirect_uri(request)
        oauth_url = get_oauth_url(
            self.scope_list, redirect_uri, extra_params=self.extra_params)

        graph = None
        try:
            # call get persistent graph and convert the
            # token with correct redirect uri
            graph = require_persistent_graph(
                request, redirect_uri=redirect_uri)
            # Note we're not requiring a persistent graph here
            # You should require a persistent graph in the view when you start
            # using this
            response = self.execute_view(
                fn, request, graph=graph, *args, **kwargs)
        except open_facebook_exceptions.OpenFacebookException, e:
            permission_granted = has_permissions(graph, self.scope_list)
            if permission_granted:
                # an error if we already have permissions
                # shouldn't have been caught
                # raise to prevent bugs with error mapping to cause issues
                raise
            elif request.REQUEST.get('attempt') == '1':
                # Doing a redirect could end up causing infinite redirects
                # If Facebook is somehow not giving permissions
                # Time to show an error page
                response = self.authentication_failed(
                    fn, request, *args, **kwargs)
            else:
                response = self.oauth_redirect(oauth_url, redirect_uri, e)
        return response


# decorators should look like functions :)
facebook_required_lazy = simplify_class_decorator(FacebookRequiredLazy)

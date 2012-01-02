from django.http import QueryDict, HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.db import models
import logging
import re
from django.utils.encoding import iri_to_uri
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


def test_permissions(request, scope_list, redirect_uri=None):
    '''
    Call Facebook me/permissions to see if we are allowed to do this
    '''
    from django_facebook.api import get_persistent_graph
    from open_facebook import exceptions as facebook_exceptions
    fb = get_persistent_graph(request, redirect_uri=redirect_uri)
    permissions_dict = {}
    if fb:
        try:
            permissions_response = fb.get('me/permissions')
            permissions = permissions_response['data'][0]
        except facebook_exceptions.OAuthException:
            # this happens when someone revokes their permissions
            # while the session is still stored
            permissions = {}
        permissions_dict = dict([(k, bool(int(v)))
                                 for k, v in permissions.items()
                                 if v == '1' or v == 1])

    # see if we have all permissions
    scope_allowed = True
    for permission in scope_list:
        if permission not in permissions_dict:
            scope_allowed = False

    # raise if this happens after a redirect though
    if not scope_allowed and request.GET.get('attempt'):
        raise ValueError(
              'Somehow facebook is not giving us the permissions needed, ' \
              'lets break instead of endless redirects. Fb was %s and ' \
              'permissions %s' % (fb, permissions_dict))

    return scope_allowed


def get_oauth_url(request, scope, redirect_uri=None, extra_params=None):
    '''
    Returns the oauth url for the given request and scope
    Request maybe shouldnt be tied to this function, but for now it seems
    rather ocnvenient
    '''
    from django_facebook import settings as facebook_settings
    scope = parse_scope(scope)
    query_dict = QueryDict('', True)
    query_dict['scope'] = ','.join(scope)
    query_dict['client_id'] = facebook_settings.FACEBOOK_APP_ID
    redirect_uri = redirect_uri or request.build_absolute_uri()

    # set attempt=1 to prevent endless redirect loops
    if 'attempt=1' not in redirect_uri:
        if '?' not in redirect_uri:
            redirect_uri += '?attempt=1'
        else:
            redirect_uri += '&attempt=1'

    # add the extra params if specified
    # TODO: renable this and fix the url merging!!
    if extra_params and False:
        # from open_facebook.utils import merge_urls
        # TODO: Properly merge the url params
        params_query_dict = QueryDict('', True)
        params_query_dict.update(extra_params)
        query_string = params_query_dict.urlencode()
        if '?' not in redirect_uri:
            redirect_uri += '?'
        else:
            redirect_uri += '&'
        redirect_uri += query_string

    query_dict['redirect_uri'] = redirect_uri
    url = 'https://www.facebook.com/dialog/oauth?'
    url += query_dict.urlencode()
    return url, redirect_uri


class CanvasRedirect(HttpResponse):
    '''
    Redirect for Facebook Canvas pages
    '''
    def __init__(self, redirect_to):
        self.redirect_to = redirect_to
        self.location = iri_to_uri(redirect_to)
        
        context = dict(location=self.location)
        js_redirect = render_to_string('django_facebook/canvas_redirect.html', context)
        
        super(CanvasRedirect, self).__init__(js_redirect)
        
def response_redirect(redirect_url, canvas=False):
    '''
    Abstract away canvas redirects
    '''
    if canvas:
        return CanvasRedirect(redirect_url)
    
    return HttpResponseRedirect(redirect_url)

def next_redirect(request, default='/', additional_params=None,
                  next_key='next', redirect_url=None, canvas=False):
    from django_facebook import settings as facebook_settings
    if facebook_settings.FACEBOOK_DEBUG_REDIRECTS:
        return HttpResponse(
            '<html><head></head><body><div>Debugging</div></body></html>')
    from django.http import HttpResponseRedirect
    if not isinstance(next_key, (list, tuple)):
        next_key = [next_key]

    # get the redirect url
    if not redirect_url:
        for key in next_key:
            redirect_url = request.REQUEST.get(key)
            if redirect_url:
                break
        if not redirect_url:
            redirect_url = default

    if additional_params:
        query_params = QueryDict('', True)
        query_params.update(additional_params)
        seperator = '&' if '?' in redirect_url else '?'
        redirect_url += seperator + query_params.urlencode()

    if canvas:
        return CanvasRedirect(redirect_url)
    
    return HttpResponseRedirect(redirect_url)


def get_profile_class():
    profile_string = settings.AUTH_PROFILE_MODULE
    app_label, model = profile_string.split('.')

    return models.get_model(app_label, model)


def mass_get_or_create(model_class, base_queryset, id_field, default_dict,
                       global_defaults):
    '''
    Updates the data by inserting all not found records
    Doesnt delete records if not in the new data

    example usage
    >>> model_class = ListItem #the class for which you are doing the insert
    >>> base_query_set = ListItem.objects.filter(user=request.user, list=1) #query for retrieving currently stored items
    >>> id_field = 'user_id' #the id field on which to check
    >>> default_dict = {'12': dict(comment='my_new_item'), '13': dict(comment='super')} #list of default values for inserts
    >>> global_defaults = dict(user=request.user, list_id=1) #global defaults
    '''
    current_instances = list(base_queryset)
    current_ids = [unicode(getattr(c, id_field)) for c in current_instances]
    given_ids = map(unicode, default_dict.keys())
    new_ids = [g for g in given_ids if g not in current_ids]
    inserted_model_instances = []
    for new_id in new_ids:
        defaults = default_dict[new_id]
        defaults[id_field] = new_id
        defaults.update(global_defaults)
        model_instance = model_class.objects.create(
            **defaults
        )
        inserted_model_instances.append(model_instance)
    # returns a list of existing and new items
    return current_instances, inserted_model_instances


def get_form_class(backend, request):
    '''
    Will use registration form in the following order:
    1. User configured RegistrationForm
    2. backend.get_form_class(request) from django-registration 0.8
    3. RegistrationFormUniqueEmail from django-registration < 0.8
    '''
    from django_facebook import settings as facebook_settings
    form_class = None

    # try the setting
    form_class_string = facebook_settings.FACEBOOK_REGISTRATION_FORM
    if form_class_string:
        form_class = get_class_from_string(form_class_string, None)

    if not form_class:
        from registration.forms import RegistrationFormUniqueEmail
        form_class = RegistrationFormUniqueEmail
        if backend:
            form_class = backend.get_form_class(request)
    return form_class


def get_registration_backend():
    '''
    Ensures compatability with the new and old version of django registration
    '''
    backend = None
    try:
        # support for the newer implementation
        from registration.backends import get_backend
        try:
            backend = get_backend(settings.REGISTRATION_BACKEND)
        except:
            raise(ValueError,
                  'Cannot get django-registration backend from ' \
                  'settings.REGISTRATION_BACKEND')
    except ImportError:
        backend = None
    return backend


def parse_scope(scope):
    '''
    Turns
    'email,user_about_me'
    or
    ('email','user_about_me')
    into a nice consistent
    ['email','user_about_me']
    '''
    assert scope, 'scope is required'
    if isinstance(scope, basestring):
        scope_list = scope.split(',')
    elif isinstance(scope, (list, tuple)):
        scope_list = list(scope)

    return scope_list


def to_int(input, default=0, exception=(ValueError, TypeError), regexp=None):
    '''Convert the given input to an integer or return default

    When trying to convert the exceptions given in the exception parameter
    are automatically catched and the default will be returned.

    The regexp parameter allows for a regular expression to find the digits
    in a string.
    When True it will automatically match any digit in the string.
    When a (regexp) object (has a search method) is given, that will be used.
    WHen a string is given, re.compile will be run over it first

    The last group of the regexp will be used as value
    '''
    if regexp is True:
        regexp = re.compile('(\d+)')
    elif isinstance(regexp, basestring):
        regexp = re.compile(regexp)
    elif hasattr(regexp, 'search'):
        pass
    elif regexp is not None:
        raise(TypeError, 'unknown argument for regexp parameter')

    try:
        if regexp:
            match = regexp.search(input)
            if match:
                input = match.groups()[-1]
        return int(input)
    except exception:
        return default


def remove_query_param(url, key):
    p = re.compile('%s=[^=&]*&' % key, re.VERBOSE)
    url = p.sub('', url)
    p = re.compile('%s=[^=&]*' % key, re.VERBOSE)
    url = p.sub('', url)
    return url


def replace_query_param(url, key, value):
    p = re.compile('%s=[^=&]*' % key, re.VERBOSE)
    return p.sub('%s=%s' % (key, value), url)


DROP_QUERY_PARAMS = ['code', 'signed_request', 'state']


def cleanup_oauth_url(redirect_uri):
    '''
    We have to maintain order with respect to the
    queryparams which is a bit of a pain
    TODO: Very hacky will subclass QueryDict to SortedQueryDict at some point
    And use a decent sort function
    '''
    if '?' in redirect_uri:
        redirect_base, redirect_query = redirect_uri.split('?', 1)
        query_dict_items = QueryDict(redirect_query).items()
    else:
        query_dict_items = QueryDict('', True)

    # filtered_query_items = [(k, v) for k, v in query_dict_items
    #                         if k.lower() not in DROP_QUERY_PARAMS]
    # new_query_dict = QueryDict('', True)
    # new_query_dict.update(dict(filtered_query_items))

    excluded_query_items = [(k, v) for k, v in query_dict_items
                            if k.lower() in DROP_QUERY_PARAMS]
    for k, v in excluded_query_items:
        redirect_uri = remove_query_param(redirect_uri, k)

    redirect_uri = redirect_uri.strip('?')
    redirect_uri = redirect_uri.strip('&')

    return redirect_uri


def get_class_from_string(path, default='raise'):
    """
    Return the class specified by the string.

    IE: django.contrib.auth.models.User
    Will return the user class

    If no default is provided and the class cannot be located
    (e.g., because no such module exists, or because the module does
    not contain a class of the appropriate name),
    ``django.core.exceptions.ImproperlyConfigured`` is raised.
    """
    from django.core.exceptions import ImproperlyConfigured
    try:
        from importlib import import_module
    except ImportError:
        from django.utils.importlib import import_module
    i = path.rfind('.')
    module, attr = path[:i], path[i + 1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured(
            'Error loading registration backend %s: "%s"' % (module, e))
    try:
        backend_class = getattr(mod, attr)
    except AttributeError:
        if default == 'raise':
            raise ImproperlyConfigured(
                'Module "%s" does not define a registration ' \
                'backend named "%s"' % (module, attr))
    return backend_class

try:
    #using compatible_datetime instead of datetime only
    #not to override the original datetime package
    from django.utils import timezone as compatible_datetime
except ImportError:
    from datetime import datetime as compatible_datetime
from datetime import datetime
from django.http import QueryDict, HttpResponse, HttpResponseRedirect
from django.conf import settings
import django.contrib.auth
from django.db import models, transaction
import logging
import re
from django_facebook import settings as facebook_settings
from django.utils.encoding import iri_to_uri
from django.template.loader import render_to_string
import gc


logger = logging.getLogger(__name__)


def clear_persistent_graph_cache(request):
    '''
    Clears the caches for the graph cache
    '''
    request.facebook = None
    request.session.delete('graph')
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        profile.clear_access_token()


def queryset_iterator(queryset, chunksize=1000, getfunc=getattr):
    '''''
    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support ordered query sets.
    '''
    pk = 0

    try:
        '''In the case of an empty list, return'''
        last_pk = getfunc(queryset.order_by('-pk')[0], 'pk')
    except IndexError:
        return

    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize].iterator():
            pk = getfunc(row, 'pk')
            yield row
        gc.collect()


def test_permissions(request, scope_list, redirect_uri=None):
    '''
    Call Facebook me/permissions to see if we are allowed to do this
    '''
    from django_facebook.api import get_persistent_graph

    fb = get_persistent_graph(request, redirect_uri=redirect_uri)
    permissions_dict = {}
    if fb:
        #see what permissions we have
        permissions_dict = fb.permissions()

    # see if we have all permissions
    scope_allowed = True
    for permission in scope_list:
        if permission not in permissions_dict:
            scope_allowed = False

    # raise if this happens after a redirect though
    if not scope_allowed and request.GET.get('attempt'):
        raise ValueError(
            'Somehow facebook is not giving us the permissions needed, '
            'lets break instead of endless redirects. Fb was %s and '
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
    current_uri = redirect_uri

    # set attempt=1 to prevent endless redirect loops
    if 'attempt=1' not in redirect_uri:
        if '?' not in redirect_uri:
            redirect_uri += '?attempt=1'
        else:
            redirect_uri += '&attempt=1'

    query_dict['redirect_uri'] = redirect_uri
    oauth_url = 'https://www.facebook.com/dialog/oauth?'
    oauth_url += query_dict.urlencode()
    return oauth_url, current_uri, redirect_uri


class CanvasRedirect(HttpResponse):
    '''
    Redirect for Facebook Canvas pages
    '''
    def __init__(self, redirect_to, show_body=True):
        self.redirect_to = redirect_to
        self.location = iri_to_uri(redirect_to)

        context = dict(location=self.location,
                       show_body=show_body)
        js_redirect = render_to_string(
            'django_facebook/canvas_redirect.html', context)

        super(CanvasRedirect, self).__init__(js_redirect)


def response_redirect(redirect_url, canvas=False):
    '''
    Abstract away canvas redirects
    '''
    if canvas:
        return CanvasRedirect(redirect_url)

    return HttpResponseRedirect(redirect_url)


def error_next_redirect(request, default='/', additional_params=None, next_key=None, redirect_url=None, canvas=False):
    '''
    Short cut for an error next redirect
    '''
    if not next_key:
        next_key = ['error_next', 'next']

    redirect = next_redirect(
        request, default, additional_params, next_key, redirect_url, canvas)
    return redirect


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


def get_user_model():
    """For Django < 1.5 backward compatibility
    """
    if hasattr(django.contrib.auth, 'get_user_model'):
        return django.contrib.auth.get_user_model()
    else:
        return django.contrib.auth.models.User


@transaction.commit_on_success
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
    current_ids = set(
        [unicode(getattr(c, id_field)) for c in current_instances])
    given_ids = map(unicode, default_dict.keys())
    #both ends of the comparison are in unicode ensuring the not in works
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
        backend = backend or get_registration_backend()
        if backend:
            form_class = backend.get_form_class(request)

    assert form_class, 'we couldnt find a form class, so we cant go on like this'

    return form_class


def get_registration_backend():
    '''
    Ensures compatability with the new and old version of django registration
    '''
    backend = None
    backend_class = None

    registration_backend_string = getattr(
        facebook_settings, 'FACEBOOK_REGISTRATION_BACKEND', None)
    if registration_backend_string:
        backend_class = get_class_from_string(registration_backend_string)

    #instantiate
    if backend_class:
        backend = backend_class()

    return backend


def get_django_registration_version():
    '''
    Returns new, old or None depending on the version of django registration
    Old works with forms
    New works with backends
    '''
    try:
        # support for the newer implementation
        from registration.backends import get_backend
        version = 'new'
    except ImportError:
        version = 'old'

    try:
        import registration
    except ImportError, e:
        version = None

    return version


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


def to_bool(input, default=False):
    '''
    Take a request value and turn it into a bool
    Never raises errors
    '''
    if input is None:
        value = default
    else:
        int_value = to_int(input, default=None)
        if int_value is None:
            value = default
        else:
            value = bool(int_value)
    return value


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


def replication_safe(f):
    '''
    Usually views which do a POST will require the next page to be
    read from the master database. (To prevent issues with replication lag).

    However certain views like login do not have this issue.
    They do a post, but don't modify data which you'll show on subsequent pages.

    This decorators marks these views as safe.
    This ensures requests on the next page are allowed to use the slave db
    '''
    from functools import wraps

    @wraps(f)
    def wrapper(request, *args, **kwargs):
        request.replication_safe = True
        response = f(request, *args, **kwargs)
        return response

    return wrapper


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
    backend_class = None
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
                'Module "%s" does not define a registration '
                'backend named "%s"' % (module, attr))
        else:
            backend_class = default
    return backend_class


def parse_like_datetime(dt):
    return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S+0000")

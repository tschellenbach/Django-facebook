from django.utils.decorators import available_attrs
from functools import wraps
try:
    # using compatible_datetime instead of datetime only
    # not to override the original datetime package
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


class NOTHING:
    pass

'''
TODO, write an abstraction class for reading and writing users/profile models
'''


def get_profile_model():
    '''
    Get the profile model if present otherwise return None
    '''
    model = None
    profile_string = getattr(settings, 'AUTH_PROFILE_MODULE', None)
    if profile_string:
        app_label, model_label = profile_string.split('.')
        model = models.get_model(app_label, model_label)
    return model


def get_user_model():
    '''
    For Django < 1.5 backward compatibility
    '''
    if hasattr(django.contrib.auth, 'get_user_model'):
        return django.contrib.auth.get_user_model()
    else:
        return django.contrib.auth.models.User


def get_model_for_attribute(attribute):
    if is_profile_attribute(attribute):
        model = get_profile_model()
    else:
        model = get_user_model()
    return model


def is_profile_attribute(attribute):
    profile_model = get_profile_model()
    profile_fields = []
    if profile_model:
        profile_fields = [f.name for f in profile_model._meta.fields]
    return attribute in profile_fields


def is_user_attribute(attribute):
    user_model = get_user_model()
    user_fields = [f.name for f in user_model._meta.fields]
    return attribute in user_fields


def get_instance_for_attribute(user, profile, attribute):
    profile_fields = []
    if profile:
        profile_fields = [f.name for f in profile._meta.fields]
    user_fields = [f.name for f in user._meta.fields]
    is_profile_field = lambda f: f in profile_fields and hasattr(profile, f)
    is_user_field = lambda f: f in user_fields and hasattr(user, f)

    instance = None
    if is_profile_field(attribute):
        instance = profile
    elif is_user_field(attribute):
        instance = user
    return instance


def get_user_attribute(user, profile, attribute, default=NOTHING):
    profile_fields = []
    if profile:
        profile_fields = [f.name for f in profile._meta.fields]
    user_fields = [f.name for f in user._meta.fields]
    is_profile_field = lambda f: f in profile_fields and hasattr(profile, f)
    is_user_field = lambda f: f in user_fields and hasattr(user, f)

    if is_profile_field(attribute):
        value = getattr(profile, attribute)
    elif is_user_field(attribute):
        value = getattr(user, attribute)
    elif default is not NOTHING:
        value = default
    else:
        raise AttributeError(
            'user or profile didnt have attribute %s' % attribute)

    return value


def update_user_attributes(user, profile, attributes_dict, save=False):
    '''
    Write the attributes either to the user or profile instance
    '''
    profile_fields = []
    if profile:
        profile_fields = [f.name for f in profile._meta.fields]
    user_fields = [f.name for f in user._meta.fields]

    is_profile_field = lambda f: f in profile_fields and hasattr(profile, f)
    is_user_field = lambda f: f in user_fields and hasattr(user, f)

    for f, value in attributes_dict.items():
        if is_profile_field(f):
            setattr(profile, f, value)
            profile._fb_is_dirty = True
        elif is_user_field(f):
            setattr(user, f, value)
            user._fb_is_dirty = True
        else:
            logger.info('skipping update of field %s', f)

    if save:
        if getattr(user, '_fb_is_dirty', False):
            user.save()
        if profile and getattr(profile, '_fb_is_dirty', False):
            profile.save()


def try_get_profile(user):
    try:
        p = user.get_profile()
    except:
        p = None
    return p


def hash_key(key):
    import hashlib
    hashed = hashlib.md5(key).hexdigest()
    return hashed


def parse_signed_request(signed_request_string):
    '''
    Just here for your convenience, actual logic is in the
    FacebookAuthorization class
    '''
    from open_facebook.api import FacebookAuthorization
    signed_request = FacebookAuthorization.parse_signed_data(
        signed_request_string)
    return signed_request


def get_url_field():
    '''
    This should be compatible with both django 1.3, 1.4 and 1.5
    In 1.5 the verify_exists argument is removed and always False
    '''
    from django.forms import URLField
    field = URLField()
    try:
        field = URLField(verify_exists=False)
    except TypeError, e:
        pass
    return field


def clear_persistent_graph_cache(request):
    '''
    Clears the caches for the graph cache
    '''
    request.facebook = None
    request.session.delete('graph')
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        profile.clear_access_token()


def has_permissions(graph, scope_list):
    from open_facebook import exceptions as open_facebook_exceptions
    permissions_granted = False
    try:
        if graph:
            permissions_granted = graph.has_permissions(scope_list)
    except open_facebook_exceptions.OAuthException, e:
        pass
    return permissions_granted


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


def get_oauth_url(scope, redirect_uri, extra_params=None):
    '''
    Returns the oAuth URL for the given scope and redirect_uri
    '''
    scope = parse_scope(scope)
    query_dict = QueryDict('', True)
    query_dict['scope'] = ','.join(scope)
    query_dict['client_id'] = facebook_settings.FACEBOOK_APP_ID

    query_dict['redirect_uri'] = redirect_uri
    oauth_url = 'https://www.facebook.com/dialog/oauth?'
    oauth_url += query_dict.urlencode()
    return oauth_url


class ScriptRedirect(HttpResponse):

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

        super(ScriptRedirect, self).__init__(js_redirect)


def response_redirect(redirect_url, script_redirect=False):
    '''
    Abstract away canvas redirects
    '''
    if script_redirect:
        return ScriptRedirect(redirect_url)

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
        return ScriptRedirect(redirect_url)

    return HttpResponseRedirect(redirect_url)


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
    # both ends of the comparison are in unicode ensuring the not in works
    new_ids = [g for g in given_ids if g not in current_ids]
    prepared_models = []
    for new_id in new_ids:
        defaults = default_dict[new_id]
        defaults[id_field] = new_id
        defaults.update(global_defaults)
        model_instance = model_class(
            **defaults
        )
        prepared_models.append(model_instance)
    # efficiently create these objects all at once
    # django 1.4 only
    if hasattr(model_class.objects, 'bulk_create'):
        model_class.objects.bulk_create(prepared_models)
    else:
        [m.save() for m in prepared_models]
    inserted_model_instances = prepared_models
    # returns a list of existing and new items
    return current_instances, inserted_model_instances


def get_form_class(backend, request):
    '''
    Will use registration form in the following order:
    1. User configured RegistrationForm
    2. backend.get_form_class(request) from django-registration 0.8
    3. RegistrationFormUniqueEmail from django-registration < 0.8
    '''
    form_class = None

    # try the setting
    form_class_string = facebook_settings.FACEBOOK_REGISTRATION_FORM
    if form_class_string:
        try:
            form_class = get_class_from_string(form_class_string, None)
        except ImportError:
            # Shouldn't this fail -- if you set it, it must be correct?
            pass

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

    # instantiate
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
    else:
        raise ValueError('unrecognized type for scope %r' % scope)

    return scope_list


def simplify_class_decorator(class_decorator):
    '''
    Makes the decorator syntax uniform
    Regardless if you call the decorator like

    **Decorator examples**::
        @decorator
        or
        @decorator()
        or
        @decorator(staff=True)

    Complexity, Python's class based decorators are weird to say the least:
    http://www.artima.com/weblogs/viewpost.jsp?thread=240845

    This function makes sure that your decorator class always gets called with

    **Methods called**::

        __init__(fn, *option_args, *option_kwargs)
        __call__()
            return a function which accepts the *args and *kwargs intended
            for fn
    '''
    # this makes sure the resulting decorator shows up as
    # function FacebookRequired instead of outer
    @wraps(class_decorator)
    def outer(fn=None, *decorator_args, **decorator_kwargs):
        # wraps isn't needed, the decorator should do the wrapping :)
        # @wraps(fn, assigned=available_attrs(fn))
        def actual_decorator(fn):
            instance = class_decorator(fn, *decorator_args, **decorator_kwargs)
            _wrapped_view = instance.__call__()
            return _wrapped_view

        if fn is not None:
            wrapped_view = actual_decorator(fn)
        else:
            wrapped_view = actual_decorator

        return wrapped_view
    return outer


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


def get_class_from_string(path, default=None):
    """
    Return the class specified by the string.

    IE: django.contrib.auth.models.User
    Will return the user class or cause an ImportError
    """
    try:
        from importlib import import_module
    except ImportError:
        from django.utils.importlib import import_module
    i = path.rfind('.')
    module, attr = path[:i], path[i + 1:]
    mod = import_module(module)
    try:
        return getattr(mod, attr)
    except AttributeError:
        if default:
            return default
        else:
            raise ImportError(
                'Cannot import name {} (from {})'.format(attr, mod))


def parse_like_datetime(dt):
    return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S+0000")


def get_default_mapping():
    from django_facebook.api import FacebookUserConverter
    DEFAULT_FACEBOOK_CLASS_MAPPING = {
        'user_conversion': FacebookUserConverter
    }
    return DEFAULT_FACEBOOK_CLASS_MAPPING


def get_class_mapping():
    mapping = facebook_settings.FACEBOOK_CLASS_MAPPING
    if mapping is None:
        mapping = get_default_mapping()
    return mapping


def get_class_for(purpose):
    '''
    Usage:
    conversion_class = get_class_for('user_conversion')
    '''
    mapping = get_class_mapping()
    class_ = mapping[purpose]
    if isinstance(class_, basestring):
        class_ = get_class_from_string(class_)
    return class_


def get_instance_for(purpose, *args, **kwargs):
    '''
    Usage:
    conversion_instance = get_instance_for(
        'facebook_user_conversion', user=user)
    '''
    class_ = get_class_for(purpose)
    instance = class_(*args, **kwargs)
    return instance

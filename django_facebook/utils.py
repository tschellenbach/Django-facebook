
from django.http import QueryDict
from django.conf import settings
from django.db import models

import logging
logger = logging.getLogger(__name__)


def get_oauth_url(request, scope, redirect_uri=None):
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
    
    #prevent redirect loops
    if '?' not in redirect_uri:
        redirect_uri += '?attempt=1'
    else:
        redirect_uri += '&attempt=1'
    logger.info('requesting access with redirect uri: %s', redirect_uri)
        
    if ('//localhost' in redirect_uri or '//127.0.0.1' in redirect_uri) and settings.DEBUG:
        raise ValueError, 'Facebook checks the domain name of your apps. Therefor you cannot run on localhost. Instead you should use something like local.fashiolista.com. Replace Fashiolista with your own domain name.'
    query_dict['redirect_uri'] = redirect_uri
    url = 'https://www.facebook.com/dialog/oauth?'
    url += query_dict.urlencode()
    return url, redirect_uri

def next_redirect(request, default='/', additional_params=None, next_key='next'):
    from django.http import HttpResponseRedirect
    if not isinstance(next_key, (list, tuple)):
        next_key = [next_key]
    
    #get the redirect url
    redirect_url = None
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
        
    return HttpResponseRedirect(redirect_url)


def get_profile_class():
    profile_string = settings.AUTH_PROFILE_MODULE
    app_label, model = profile_string.split('.')

    return models.get_model(app_label, model)
    
    
def mass_get_or_create(model_class, base_queryset, id_field, default_dict, global_defaults):
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
        
    #returns a list of existing and new items
    return current_instances, inserted_model_instances


def get_registration_backend():
    '''
    Ensures compatability with the new and old version of django registration
    '''
    backend = None
    try:        
        #support for the newer implementation
        from registration.backends import get_backend
        try:
            backend = get_backend(settings.REGISTRATION_BACKEND)
        except:
            raise ValueError, 'Cannot get django-registration backend from settings.REGISTRATION_BACKEND'
    except ImportError, e:
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
    import re
    if regexp is True:
        regexp = re.compile('(\d+)')
    elif isinstance(regexp, basestring):
        regexp = re.compile(regexp)
    elif hasattr(regexp, 'search'):
        pass
    elif regexp is not None:
        raise TypeError, 'unknown argument for regexp parameter'

    try:
        if regexp:
            match = regexp.search(input)
            if match:
                input = match.groups()[-1]
        return int(input)
    except exception:
        return default
    
    

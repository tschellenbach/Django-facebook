
from django.http import QueryDict
from django.conf import settings
from django.contrib.contenttypes.models import ContentType




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
    #TODO: isn't there a dedicated function for this in django somewhere?
    profile_string = settings.AUTH_PROFILE_MODULE
    profile_model = profile_string.split('.')[-1]
    profile_class = ContentType.objects.get(model=profile_model.lower()).model_class()
    return profile_class
    
    
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

    
    

from django.http import QueryDict
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.loading import get_model

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
    profile_model = settings.AUTH_PROFILE_MODULE.lower().split('.') # get_model takes lowercased arguments
    profile_class = get_model(profile_model[0],profile_model[1]) # get_model(app_name,model_class_name)
    if profile_class == None:
        raise Exception('Could not get profile class.')
    return profile_class
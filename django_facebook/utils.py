from django.http import QueryDict





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

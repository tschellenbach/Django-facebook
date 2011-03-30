from django.http import QueryDict





def next_redirect(request, default='/', additional_params=None):
    from django.http import HttpResponseRedirect
    redirect_url = request.REQUEST.get('next', default)
    if additional_params:
        query_params = QueryDict('', True)
        query_params.update(additional_params)
        seperator = '&' if '?' in redirect_url else '?'
        redirect_url += seperator + query_params.urlencode()
        
    return HttpResponseRedirect(redirect_url)

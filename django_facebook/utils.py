




def next_redirect(request, default='/'):
    from django.http import HttpResponseRedirect
    redirect_url = request.REQUEST.get('next', default)
    return HttpResponseRedirect(redirect_url)

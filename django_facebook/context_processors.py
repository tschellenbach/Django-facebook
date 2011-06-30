from django_facebook.api import get_facebook_graph

def facebook(request):
    context = {}
    from django_facebook import settings as facebook_settings
    context['FACEBOOK_API_KEY'] = facebook_settings.FACEBOOK_API_KEY
    context['FACEBOOK_APP_ID'] = facebook_settings.FACEBOOK_APP_ID
    context['facebook'] = get_facebook_graph(request)
    
    return context
def facebook(request):
    context = {}
    from django_facebook import settings as facebook_settings
    context['FACEBOOK_APP_ID'] = facebook_settings.FACEBOOK_APP_ID
    context['FACEBOOK_DEFAULT_SCOPE'] = facebook_settings.FACEBOOK_DEFAULT_SCOPE
    
    return context
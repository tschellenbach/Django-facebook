def facebook(request):
    context = {}
    from django_facebook import settings as facebook_settings
    context['FACEBOOK_APP_ID'] = facebook_settings.FACEBOOK_APP_ID
    
    return context
from django.utils.safestring import mark_safe

def facebook(request):
    context = {}
    from django_facebook import settings as facebook_settings
    from open_facebook.utils import json
    context['FACEBOOK_APP_ID'] = facebook_settings.FACEBOOK_APP_ID
    context['FACEBOOK_DEFAULT_SCOPE'] = facebook_settings.FACEBOOK_DEFAULT_SCOPE
    
    default_scope_js = unicode(json.dumps(facebook_settings.FACEBOOK_DEFAULT_SCOPE))
    default_scope_js = mark_safe(default_scope_js)
    context['FACEBOOK_DEFAULT_SCOPE_JS'] = default_scope_js
    
    return context
from django.utils.safestring import mark_safe


def facebook(request):
    context = {}
    from django_facebook import settings as fb_settings
    from open_facebook.utils import json
    context['FACEBOOK_APP_ID'] = fb_settings.FACEBOOK_APP_ID
    context['FACEBOOK_DEFAULT_SCOPE'] = fb_settings.FACEBOOK_DEFAULT_SCOPE

    default_scope_js = unicode(json.dumps(
        fb_settings.FACEBOOK_DEFAULT_SCOPE))
    default_scope_js = mark_safe(default_scope_js)
    context['FACEBOOK_DEFAULT_SCOPE_JS'] = default_scope_js

    return context

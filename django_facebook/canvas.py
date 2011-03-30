from django.http import QueryDict
from django_facebook import settings as facebook_settings




def generate_oauth_url(scope='email,read_stream', extra_data=None):
    query_dict = QueryDict('', True)
    canvas_page = facebook_settings.FACEBOOK_CANVAS_PAGE
    query_dict.update(dict(client_id=facebook_settings.FACEBOOK_APP_ID, redirect_uri=canvas_page, scope=scope))
    if extra_data:
        query_dict.update(extra_data)
    auth_url = 'http://www.facebook.com/dialog/oauth?%s' % (query_dict.urlencode(),)
    return auth_url

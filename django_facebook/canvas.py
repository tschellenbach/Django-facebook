from django.http import QueryDict
from django_facebook import settings as facebook_settings


def generate_oauth_url(scope=facebook_settings.FACEBOOK_DEFAULT_SCOPE,
                       next=None, extra_data=None):
    query_dict = QueryDict('', True)
    canvas_page = (next if next is not None else
                   facebook_settings.FACEBOOK_CANVAS_PAGE)
    query_dict.update(dict(client_id=facebook_settings.FACEBOOK_APP_ID,
                           redirect_uri=canvas_page, scope=scope))
    if extra_data:
        query_dict.update(extra_data)
    auth_url = 'http://www.facebook.com/dialog/oauth?%s' % (
        query_dict.urlencode(), )
    return auth_url

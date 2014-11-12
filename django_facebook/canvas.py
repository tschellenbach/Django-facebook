from django.http import QueryDict
from django_facebook import settings as facebook_settings


def generate_oauth_url(scope=facebook_settings.FACEBOOK_DEFAULT_SCOPE,
                       next=None, extra_data=None, *args, **kwargs):
    query_dict = QueryDict('', True)
    facebook_app_id = kwargs.get(facebook_settings.FACEBOOK_APP_ID_KWARGS,
                                facebook_settings.FACEBOOK_APP_ID)
    facebook_canvas_page = kwargs.get(facebook_settings.FACEBOOK_CANVAS_PAGE_KWARGS,
                                    facebook_settings.FACEBOOK_CANVAS_PAGE)
    canvas_page = (next if next is not None else facebook_canvas_page)
    query_dict.update(dict(client_id=facebook_app_id,
                           redirect_uri=canvas_page,
                           scope=','.join(scope)))
    if extra_data:
        query_dict.update(extra_data)
    auth_url = 'https://www.facebook.com/dialog/oauth?%s' % (
        query_dict.urlencode(), )
    return auth_url

# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

import django
import mock
import urllib2

from open_facebook import OpenFacebook

### To emulate ``from django_facebook.api import get_facebook_graph``
### use the following decorators on your test cases
###
### @mock.patch('your_project.auth.get_facebook_graph', new=mock_facebook_objects.get_mock_facebook_graph)
### @mock.patch('your_project.web.user_views.get_facebook_graph', new=mock_facebook_objects.get_mock_facebook_graph)
### @mock.patch('open_facebook.api.OpenFacebook.request', new=mock_facebook_objects.mock_request_json_other)

mock_facebook_graph = mock.Mock(name='mock_facebook_graph', spec=OpenFacebook, wraps=OpenFacebook())

mock_facebook_graph.access_token = '123'

get_mock_facebook_graph = mock.Mock(name='mock_get_facebook_graph', return_value=mock_facebook_graph)

def mock_request_side_effect(path = '', post_data = None, old_api = False, **params):
    if path == 'me':
        return {
            'id': 123,
            'link': '/jameskala',
            'email': 'james.kala@fb.example.com',
            'first_name': 'james',
            'last_name': 'kala',
            'city': 'helsinki', }
    elif path == 'fql.query':
        # assuming that this happens due to a get_friends query in django_facebook api
        return { }
    elif path == '':
        return { }
    else:
        assert False

mock_request_json = mock.Mock(name='mock_request_json', side_effect=mock_request_side_effect)

mock_facebook_graph_other = mock.Mock(name='mock_facebook_graph', spec=OpenFacebook, wraps=OpenFacebook())

mock_facebook_graph_other.access_token = '321'

get_mock_facebook_graph_other = mock.Mock(name='mock_get_facebook_graph', return_value=mock_facebook_graph_other)

def mock_request_side_effect_other(path = '', post_data = None, old_api = False, **params):
    if path == 'me':
        return {
            'id': 512,
            'link': '/jormapomo',
            'email': 'jorma.pomo@example.com',
            'first_name': 'jorma',
            'last_name': 'pomo', }
    elif path == 'fql.query':
        # assuming that this happens due to a get_friends query in django_facebook api
        return { }
    elif path == '':
        return { }
    else:
        assert False

mock_request_json_other = mock.Mock(name='mock_request_json', side_effect=mock_request_side_effect_other)

mock_facebook_graph_error = mock.Mock(name='mock_facebook_graph', spec=OpenFacebook, wraps=OpenFacebook())

mock_facebook_graph_error.access_token = '323'

get_mock_facebook_graph_error = mock.Mock(name='mock_get_facebook_graph', return_value=mock_facebook_graph_error)

mock_request_json_error = mock.Mock(name='mock_request_json_error', side_effect=urllib2.HTTPError('',501,'','',None))


# EOF


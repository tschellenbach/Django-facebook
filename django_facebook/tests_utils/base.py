from django.core.handlers.base import BaseHandler
from django.test import TestCase
from django.test.client import Client, RequestFactory


class RequestMock(RequestFactory):
    '''
    Didn't see another solution for this. Decided to read some snippets
    and modded them into the requestfactory class
    http://www.mellowmorning.com/2011/04/18/mock-django-request-for-testing/
    '''
    def request(self, **request):
        "Construct a generic request object."
        request['REQUEST'] = dict()
        request = RequestFactory.request(self, **request)
        handler = BaseHandler()
        handler.load_middleware()
        for middleware_method in handler._request_middleware:
            if middleware_method(request):
                raise Exception("Couldn't create request mock object - "
                                "request middleware returned a response")
        return request


class FacebookTest(TestCase):
    '''
    Normal Facebook tests run against a fake API
    '''
    def setUp(self):
        from django_facebook.tests_utils.mock_official_sdk import MockFacebookAPI, MockFacebookAuthorization
        from open_facebook import api
        import open_facebook

        self.originalAPI = open_facebook.OpenFacebook
        self.originalAuthorization = open_facebook.FacebookAuthorization

        open_facebook.OpenFacebook = api.OpenFacebook = MockFacebookAPI
        open_facebook.FacebookAuthorization = api.FacebookAuthorization = MockFacebookAuthorization

        rf = RequestMock()
        self.request = rf.get('/')
        self.client = Client()

    def tearDown(self):
        from open_facebook import api
        import open_facebook
        open_facebook.OpenFacebook = api.OpenFacebook = self.originalAPI
        open_facebook.FacebookAuthorization = api.FacebookAuthorization = self.originalAuthorization
        
    def create_patch(self, name, return_value=None):
        '''
        Easy workaround for having to nest mock.patch context managers
        '''
        from mock import patch
        patcher = patch(name)
        thing = patcher.start()
        if return_value is not None:
            thing.return_value = return_value
        self.addCleanup(patcher.stop)
        return thing
    
    def mock_authenticated(self):
        '''
        Fake that we are authenticated
        '''
        self.create_patch('django_facebook.decorators.has_permissions', True)
        self.create_patch('django_facebook.decorators.get_persistent_graph', True)
        self.create_patch('django_facebook.decorators.require_persistent_graph', True)


class LiveFacebookTest(TestCase):
    '''
    Live Facebook Tests run against the actual Facebook API
    '''
    pass

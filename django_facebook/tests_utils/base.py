from django.core.handlers.base import BaseHandler
from django.test.client import RequestFactory
from django.test import TestCase


class RequestMock(RequestFactory):
    '''
    Didn't see another solution for this. Decided to read some snippets
    and modded them into the requestfactory class
    http://www.mellowmorning.com/2011/04/18/mock-django-request-for-testing/
    '''
    def request(self, **request):
        "Construct a generic request object."
        request = RequestFactory.request(self, **request)
        handler = BaseHandler()
        handler.load_middleware()
        for middleware_method in handler._request_middleware:
            if middleware_method(request):
                raise Exception("Couldn't create request mock object - "
                                "request middleware returned a response")
        return request


class FacebookTest(TestCase):
    def setUp(self):
        from django_facebook.tests_utils.mock_official_sdk import MockFacebookAPI
        from open_facebook import api
        import open_facebook
        api.OpenFacebook = MockFacebookAPI
        open_facebook.OpenFacebook = MockFacebookAPI

        rf = RequestMock()
        self.request = rf.get('/')

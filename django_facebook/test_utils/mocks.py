from django.test.client import RequestFactory
from open_facebook.api import OpenFacebook, FacebookAuthorization
from django.core.handlers.base import BaseHandler


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


class MockFacebookAPI(OpenFacebook):
    mock = True

    def me(self):
        from django_facebook.test_utils.sample_user_data import user_data
        data = user_data[self.access_token]
        return data

    def my_image_url(self, size=None):
        from django_facebook.test_utils.sample_user_data import user_data
        data = user_data[self.access_token]
        image_url = data['image']
        return image_url

    def is_authenticated(self, *args, **kwargs):
        from django_facebook.test_utils.sample_user_data import user_data
        return self.access_token in user_data

    def get(self, path, **kwargs):
        if 'likes' in path:
            like = dict(
                name="Vogue Nederland", category="Media/news/publishing", id="136067283169158")
            response = dict(data=[like])
            return response
        if 'friends' or 'friend' in path:
            friend = dict(name="Aida Tavakkolie", id="172001264")
            response = dict(data=[friend])
            return response

    def set(self, path, **kwargs):
        return dict(id=123456789)

    def fql(self, query, **kwargs):
        """Runs the specified query against the Facebook FQL API.
        """
        friend = dict(name="Aida Tavakkolie", uid=172001264, gender='F')
        response = [friend]

        return response


class MockFacebookAuthorization(FacebookAuthorization):

    @classmethod
    def extend_access_token(cls, access_token):
        '''
        https://developers.facebook.com/roadmap/offline-access-removal/
        We can extend the token only once per day
        Normal short lived tokens last 1-2 hours
        Long lived tokens (given by extending) last 60 days
        '''
        response = dict(access_token=access_token, expires='123456789')
        return response

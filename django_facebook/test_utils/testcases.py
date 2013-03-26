from django.test import TestCase
from django.test.client import Client


class FacebookTest(TestCase):
    '''
    Normal Facebook tests run against a fake API
    '''
    def setUp(self):
        from django_facebook.test_utils.mocks import MockFacebookAPI, MockFacebookAuthorization, RequestMock

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
        from django_facebook.test_utils.mocks import MockFacebookAPI, MockFacebookAuthorization, RequestMock
        graph = MockFacebookAPI('short_username')
        self.create_patch('django_facebook.decorators.has_permissions', True)
        self.create_patch(
            'django_facebook.connect.get_facebook_graph', graph)
        self.create_patch(
            'django_facebook.decorators.get_persistent_graph', graph)
        self.create_patch(
            'django_facebook.decorators.require_persistent_graph', graph)


class LiveFacebookTest(TestCase):
    '''
    Live Facebook Tests run against the actual Facebook API
    '''
    pass

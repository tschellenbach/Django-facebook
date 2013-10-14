from django.test import TestCase
from django.test.client import Client
from django_facebook.utils import get_user_model, is_user_attribute


class FacebookTest(TestCase):

    '''
    Normal Facebook tests run against a fake API
    '''

    def setUp(self):
        from django_facebook.test_utils.mocks import MockFacebookAPI, MockFacebookAuthorization, RequestMock
        import sys
        import StringIO
        self.prints = sys.stdout = StringIO.StringIO()

        from open_facebook import api
        import open_facebook

        self.originalAPI = open_facebook.OpenFacebook
        self.originalAuthorization = open_facebook.FacebookAuthorization

        open_facebook.OpenFacebook = api.OpenFacebook = MockFacebookAPI
        open_facebook.FacebookAuthorization = api.FacebookAuthorization = MockFacebookAuthorization

        rf = RequestMock()
        self.request = rf.get('/')
        self.client = Client()

        # time to setup the test user
        user_model = get_user_model()
        user_dict = dict(
            username='tschellenbach',
            is_staff=False,
            is_active=True,
            email="fake@mellowmorning.com",
        )
        test_ip = '127.0.0.1'
        # hack to make fashiolista tests run ok
        if is_user_attribute('registration_ip'):
            user_dict['registration_ip'] = test_ip
            user_dict['last_login_ip'] = test_ip
        user_model.objects.create(**user_dict)

        from django.conf import settings
        if getattr(settings, 'MODE', None) == 'userena':
            from django.core.management import call_command
            call_command('check_permissions', output=False)

    def tearDown(self):
        from open_facebook import api
        import open_facebook
        open_facebook.OpenFacebook = api.OpenFacebook = self.originalAPI
        open_facebook.FacebookAuthorization = api.FacebookAuthorization = self.originalAuthorization

        self.prints.seek(0)
        content = self.prints.read()
        if content:
            raise ValueError('print statement found, output %s' % content)

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

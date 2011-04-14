from django_facebook.api import FacebookAPI



class MockFacebookAPI(FacebookAPI):
    def get_object(self, id, **args):
        print 'getting object'
        assert id == 'me'
        from django_facebook.tests.sample_data.user_data import user_data
        return user_data[self.access_token]
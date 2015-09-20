from datetime import datetime
from django_facebook.test_utils.testcases import FacebookTest
from django_facebook.utils import get_user_model, try_get_profile
from .views import timestamp_visit_view
from .models import VisitTimestamp


class VisitTimestampTest(FacebookTest):
    def setUp(self):
        FacebookTest.setUp(self)
        self.url = "/picked_date"
        user = get_user_model().objects.all()[:1][0]
        profile = try_get_profile(user)
        user.get_profile = lambda: profile
        self.request.user = user

    def test(self):
        self.mock_authenticated()
        response = timestamp_visit_view(self.request)
        timestamp = VisitTimestamp.objects.all()[:1][0].date_time.replace(tzinfo=None)
        assert (datetime.now() - timestamp).total_seconds() < 1000
        assert response.status_code == 302


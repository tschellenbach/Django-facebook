from datetime import datetime
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django_facebook.decorators import facebook_required
from .models import VisitTimestamp


@facebook_required
def timestamp_visit_view(request):
    date_time = datetime.now()
    profile = request.user.get_profile()
    visit = VisitTimestamp(
        visitor_profile=profile,
        date_time=date_time
    )
    visit.save()
    return HttpResponseRedirect("/")

def home_view(request):
    num_visits = VisitTimestamp.objects.all().count()
    return render(request, 'home.html', {"num_visits": num_visits})

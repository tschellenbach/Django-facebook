# -*- coding: UTF-8 -*-
from django_facebook.management.commands.base import CustomBaseCommand
from django_facebook.utils import get_profile_class

class Command(CustomBaseCommand):
    help = '''Mark fb_require_update flag for all profiles. 
    Use this if you add a new permission like birth_date and need to update all profiles upon login.
    Use it with ./manage.py reset sessions to force every user to login with django again'''

    def handle(self, *args, **kwargs):
        super(Command, self).handle(*args, **kwargs)
        profile = get_profile_class()
        updates = profile.objects.update(fb_update_required=True)
        
        print "%s profiles updated" % updates 
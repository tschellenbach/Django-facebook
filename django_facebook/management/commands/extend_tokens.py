from django_facebook.management.commands.base import CustomBaseCommand
from django_facebook.utils import queryset_iterator
from optparse import make_option
import datetime


class ExtendTokensCommand(CustomBaseCommand):
    help = 'Extend all the users access tokens\'s, per hour'
    option_list = CustomBaseCommand.option_list + (
        make_option('--all',
                    action='store_true',
                    dest='all',
                    default=False,
                    help='Extend all of them at once'
                    ),
    )

    def handle(self, *args, **kwargs):

        queryset_iterator

from django.core.management.base import BaseCommand
import logging
import sys

DEFAULT_VERBOSITY = 1
VERBOSITY_LOG_MAP = {
    0: logging.WARN,
    1: logging.INFO,
    2: logging.DEBUG,
    3: logging.DEBUG,
}


class CustomBaseCommand(BaseCommand):

    '''
    Management command with a convenient self.log.info shortcut allowing for
    easy logging

    Listens to the verbosity command given to the management command
    '''

    def __init__(self, session=None):
        self._session = session
        self.verbosity = DEFAULT_VERBOSITY
        BaseCommand.__init__(self)

    def handle(self, *args, **kwargs):
        self.verbosity = int(kwargs.get('verbosity', DEFAULT_VERBOSITY))

    def create_logger(self):
        name = self.__class__.__module__.split('.')[-1]

        logger_name = 'management.commands.%s' % name
        logger = logging.getLogger(logger_name)
        logger.extra = {
            'view': logger_name,
            'data': {
                'command': ' '.join(sys.argv),
            }
        }

        handler = logging.StreamHandler()
        logger.addHandler(handler)
        logger.setLevel(VERBOSITY_LOG_MAP[self.verbosity])
        return logger

    @property
    def log(self):
        if not hasattr(self, 'logger'):
            self.logger = self.create_logger()
        return self.logger

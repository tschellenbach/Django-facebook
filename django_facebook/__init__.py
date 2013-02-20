__author__ = 'Thierry Schellenbach'
__copyright__ = 'Copyright 2010, Thierry Schellenbach'
__credits__ = ['Thierry Schellenbach, mellowmorning.com, @tschellenbach']


__license__ = 'BSD'
__version__ = '5.0.2prealpha'
__maintainer__ = 'Thierry Schellenbach'
__email__ = 'thierryschellenbach@gmail.com'
__status__ = 'Production'

'''
Some links which help me with publishing this code

rest editor
http://rst.ninjs.org/

updating pypi
python setup.py sdist upload
http://pypi.python.org/pypi

setting up pip for editing
http://www.pip-installer.org/en/latest/index.html
pip install -e ./
'''

import logging
logger = logging.getLogger(__name__)

try:
    from django_facebook.api import get_persistent_graph
    from django_facebook.api import require_persistent_graph
    from django_facebook.decorators import facebook_required
    from django_facebook.decorators import facebook_required_lazy
except ImportError, e:
    logger.warn('Couldnt import django_facebook shortcuts, errors was %s', e)
    #TODO ugly hack for running pip install (django isnt available at that point)
    pass

# This file mainly exists to allow python setup.py test to work.
import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'facebook_example.settings'

#add the example project to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
example_path = os.path.join(current_dir, 'facebook_example')
sys.path.insert(0, example_path)

from django.test.utils import get_runner
from django.conf import settings


# run the tests
# or should we use http://pypi.python.org/pypi/django-setuptest?
def runtests():
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=True)
    failures = test_runner.run_tests(['django_facebook'])
    sys.exit(bool(failures))

runtests()
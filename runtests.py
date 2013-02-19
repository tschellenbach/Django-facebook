import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
example_dir = os.path.join(current_dir, 'facebook_example')

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'facebook_example.settings'
    DJANGO_SETTINGS_MODULE = 'facebook_example.settings'


def runtests(args=None):
    import pytest
    sys.path.append(example_dir)

    if not args:
        args = []

    if not any(a for a in args[1:] if not a.startswith('-')):
        args.append('tests')

    result = pytest.main(['django_facebook', 'open_facebook'])
    sys.exit(result)


if __name__ == '__main__':
    runtests(sys.argv)

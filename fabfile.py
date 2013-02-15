from fabric.api import local, cd
from facebook_example.settings import BASE_ROOT
import os
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_ROOT, '../'))


def publish(test='yes'):
    '''
    Easy publishing of my nice open source project
    '''
    if test == 'yes':
        validate()

    local('git push')

    from django_facebook import __version__
    tag_name = 'v%s' % __version__
    local('python setup.py sdist upload')

    local('git tag %s' % tag_name)
    local('git push origin --tags')


def validate():
    with cd(PROJECT_ROOT):
        local('pep8 --exclude=migrations --ignore=E501,E225 django_facebook open_facebook')
        local('facebook_example\manage.py test open_facebook django_facebook')


def clean():
    local('bash -c "autopep8 -i *.py"')
    local('bash -c "autopep8 -i django_facebook/*.py"')
    local('bash -c "autopep8 -i open_facebook/*.py"')
    local('bash -c "autopep8 -i django_facebook/management/commands/*.py"')
    local('bash -c "autopep8 -i django_facebook/tests_utils/*.py"')

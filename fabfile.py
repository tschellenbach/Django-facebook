from fabric.api import local, cd
import os
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
manage_py = os.path.join('facebook_example', 'manage.py')


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
        local(
            'pep8 --exclude=migrations --ignore=E501,E225 django_facebook open_facebook')
        local('python %s test open_facebook django_facebook' % manage_py)


def full_validate():
    with cd(PROJECT_ROOT):
        local(
            'pep8 --exclude=migrations --ignore=E501,E225 django_facebook open_facebook')
        local('CUSTOM_USER_MODEL=0 python %s test open_facebook django_facebook' %
              manage_py)
        local('CUSTOM_USER_MODEL=1 python %s test open_facebook django_facebook' %
              manage_py)
        local('CUSTOM_USER_MODEL=0 MODE=userena python %s test open_facebook django_facebook' %
              manage_py)


def clean():
    local('bash -c "autopep8 -i *.py"')
    local('bash -c "autopep8 -i django_facebook/*.py"')
    local('bash -c "autopep8 -i open_facebook/*.py"')
    local('bash -c "autopep8 -i django_facebook/management/commands/*.py"')
    local('bash -c "autopep8 -i django_facebook/test_utils/*.py"')


def docs():
    local('sphinx-build -Eav docs html')

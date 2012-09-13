from fabric.api import local


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
    local('pep8 --exclude=migrations --ignore=E501,E225 django_facebook open_facebook')
    local('facebook_example\manage.py test django_facebook')


def clean():
    local('autopep8 -i *.py')
    local('autopep8 -i django_facebook/*.py')
    local('autopep8 -i open_facebook/*.py')

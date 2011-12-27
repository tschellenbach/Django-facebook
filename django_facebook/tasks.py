from celery import task
import logging
logger = logging.getLogger(__name__)


@task.task(ignore_result=True)
def store_likes(user, likes):
    from django_facebook.api import FacebookUserConverter
    logger.info('celery is storing %s likes' % len(likes))
    FacebookUserConverter._store_likes(user, likes)
    return likes


@task.task(ignore_result=True)
def get_and_store_likes(user, facebook):
    '''
    Since facebook is quite slow this version also runs the get
    on the background
    '''
    stored_likes = facebook._get_and_store_likes(user)
    logger.info('celery is storing %s likes' % len(stored_likes))
    return stored_likes


@task.task(ignore_result=True)
def store_friends(user, friends):
    from django_facebook.api import FacebookUserConverter
    logger.info('celery is storing %s friends' % len(friends))
    FacebookUserConverter._store_friends(user, friends)
    return friends


@task.task(ignore_result=True)
def get_and_store_friends(user, facebook):
    '''
    Since facebook is quite slow this version also runs the get
    on the background
    '''
    stored_friends = facebook._get_and_store_friends(user)
    logger.info('celery is storing %s friends' % len(stored_friends))
    return stored_friends


@task.task()
def async_connect_user(request, graph):
    '''
    Runs the whole connect flow in the background.
    Saving your webservers from facebook fluctuations
    '''
    pass

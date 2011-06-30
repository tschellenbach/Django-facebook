from celery import task
import logging
logger = logging.getLogger(__name__)



@task.task(ignore_result=True)
def store_likes(user, likes):
    from django_facebook.api import FacebookAPI
    logger.info('celery is storing %s likes' % len(likes))
    FacebookAPI._store_likes(user, likes)
    
    return likes


@task.task(ignore_result=True)
def store_friends(user, friends):
    from django_facebook.api import FacebookAPI
    logger.info('celery is storing %s friends' % len(friends))
    FacebookAPI._store_friends(user, friends)
    
    return friends




from celery import task
from django.db import IntegrityError
import logging
import urllib
import urllib2
logger = logging.getLogger(__name__)


@task.task(ignore_result=True)
def store_likes(user, likes):
    '''
    Inserting again will not cause any errors, so this is safe
    for multiple executions

    :param user: The user for which we are storing
    :type user: User object
    
    :param friends: List of your likes
    :type friends: list
    '''
    from django_facebook.api import FacebookUserConverter
    logger.info('celery is storing %s likes' % len(likes))
    FacebookUserConverter._store_likes(user, likes)
    return likes


@task.task(ignore_result=True)
def get_and_store_likes(user, facebook):
    '''
    Since facebook is quite slow this version also runs the get
    on the background
    
    Inserting again will not cause any errors, so this is safe
    for multiple executions

    :param user: The user for which we are storing
    :type user: User object
    
    :param facebook: The graph connection to facebook
    :type facebook: FacebookUserConverter object
    '''
    try:
        logger.info('attempting to get and store friends for %s', user.id)
        stored_likes = facebook._get_and_store_likes(user)
        logger.info('celery is storing %s likes', len(stored_likes))
        return stored_likes
    except IntegrityError, e:
        logger.warn('get_and_store_likes failed for %s with error %s', user.id, e)


@task.task(ignore_result=True)
def store_friends(user, friends):
    '''
    Inserting again will not cause any errors, so this is safe
    for multiple executions

    :param user: The user for which we are storing
    :type user: User object
    
    :param friends: List of your friends
    :type friends: list
    '''
    from django_facebook.api import FacebookUserConverter
    logger.info('celery is storing %s friends' % len(friends))
    FacebookUserConverter._store_friends(user, friends)
    return friends


@task.task(ignore_result=True)
def get_and_store_friends(user, facebook):
    '''
    Since facebook is quite slow this version also runs the get
    on the background
    
    Inserting again will not cause any errors, so this is safe
    for multiple executions

    :param user: The user for which we are storing
    :type user: User object
    
    :param facebook: The graph connection to facebook
    :type facebook: FacebookUserConverter object
    '''
    try:
        logger.info('attempting to get and store friends for %s', user.id)
        stored_friends = facebook._get_and_store_friends(user)
        logger.info('celery is storing %s friends', len(stored_friends))
        return stored_friends
    except IntegrityError, e:
        logger.warn('get_and_store_friends failed for %s with error %s', user.id, e)

@task.task()
def extend_access_token(profile,access_token):
    q = {
            "client_id": settings.FACEBOOK_APP_ID,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "grant_type": "fb_exchange_token",
            "fb_exchange_token": access_token,
        }
    response = urllib2.urlopen('https://graph.facebook.com/oauth/access_token?%s' % urllib.urlencode(q)).read()
    # returns a str object instead of json for some reason ...
    token = response.split('&', 1)[0].split('=')[1]
    profile.extended_access_token = token
    profile.save()

@task.task()
def async_connect_user(request, graph):
    '''
    Runs the whole connect flow in the background.
    Saving your webservers from facebook fluctuations
    
    Currently this has not yet been implemented.
    It will be possible to run this command 1-N times
    '''
    pass

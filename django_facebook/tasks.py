from celery import task
from django.db import IntegrityError
import logging
from django_facebook.utils import get_class_for

logger = logging.getLogger(__name__)


@task.task(ignore_result=True)
def extend_access_token(profile, access_token):
    results = profile._extend_access_token(access_token)
    return results


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
    converter_class = get_class_for('user_conversion')
    logger.info('celery is storing %s likes' % len(likes))
    converter_class._store_likes(user, likes)
    return likes


@task.task(ignore_result=True)
def remove_share(share):
    share._remove()


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
        logger.warn(
            'get_and_store_likes failed for %s with error %s', user.id, e)


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
    converter_class = get_class_for('user_conversion')
    logger.info('celery is storing %s friends' % len(friends))
    converter_class._store_friends(user, friends)
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
        logger.warn(
            'get_and_store_friends failed for %s with error %s', user.id, e)


@task.task(ignore_result=True)
def retry_open_graph_share(share, reset_retries=False):
    '''
    We will retry open graph shares after 15m to make sure we dont miss out on any
    shares if Facebook is having a minor outage
    '''
    logger.info('retrying open graph share %s', share)
    share.retry(reset_retries=reset_retries)


@task.task(ignore_result=True)
def retry_open_graph_shares_for_user(user):
    '''
    We retry the open graph shares for a user when he gets a new access token
    '''
    from django_facebook.models import OpenGraphShare
    shares = OpenGraphShare.objects.recently_failed().filter(user=user)[:1000]
    shares = list(shares)
    logger.info('retrying %s shares for user %s', len(shares), user)

    for share in shares:
        retry_open_graph_share(share, reset_retries=True)


def token_extended_connect(sender, user, profile, token_changed, old_token, **kwargs):
    from django_facebook import settings as facebook_settings
    if facebook_settings.FACEBOOK_CELERY_TOKEN_EXTEND:
        # This is only save to run if we are using Celery
        # make sure we don't have troubles caused by replication lag
        retry_open_graph_shares_for_user.apply_async(args=[user], countdown=60)

from django_facebook.signals import facebook_token_extend_finished
facebook_token_extend_finished.connect(token_extended_connect)

import logging
from random import randint
import sys

from django.contrib import auth
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import simplejson as json

from django_facebook import settings as facebook_settings
from django_facebook import exceptions as facebook_exceptions
from django_facebook import signals
from django_facebook.api import get_facebook_graph, FacebookUserConverter
from django_facebook.utils import (get_registration_backend, get_form_class,
                                   get_profile_class)

logger = logging.getLogger(__name__)


class CONNECT_ACTIONS:
    class LOGIN:
        pass

    class CONNECT(LOGIN):
        pass

    class REGISTER:
        pass


def connect_user(request, access_token=None, facebook_graph=None):
    '''
    Given a request either

    - (if authenticated) connect the user
    - login
    - register
    '''
    user = None
    graph = facebook_graph or get_facebook_graph(request, access_token)
    facebook = FacebookUserConverter(graph)

    assert facebook.is_authenticated()
    facebook_data = facebook.facebook_profile_data()
    force_registration = request.REQUEST.get('force_registration') or\
        request.REQUEST.get('force_registration_hard')

    logger.debug('force registration is set to %s', force_registration)
    if request.user.is_authenticated() and not force_registration:
        action = CONNECT_ACTIONS.CONNECT
        user = _connect_user(request, facebook)
    else:
        email = facebook_data.get('email', False)
        email_verified = facebook_data.get('verified', False)
        kwargs = {}
        if email and email_verified:
            kwargs = {'facebook_email': email}
        auth_user = authenticate(facebook_id=facebook_data['id'], **kwargs)
        if auth_user and not force_registration:
            action = CONNECT_ACTIONS.LOGIN

            # Has the user registered without Facebook, using the verified FB
            # email address?
            # It is after all quite common to use email addresses for usernames
            if not auth_user.get_profile().facebook_id:
                update = True
            else:
                update = getattr(auth_user, 'fb_update_required', False)
            user = _login_user(request, facebook, auth_user, update=update)
        else:
            action = CONNECT_ACTIONS.REGISTER
            # when force registration is active we should clearout
            # the old profile
            user = _register_user(request, facebook,
                                  remove_old_connections=force_registration)

    #store likes and friends if configured
    sid = transaction.savepoint()
    try:
        if facebook_settings.FACEBOOK_STORE_LIKES:
            facebook.get_and_store_likes(user)
        if facebook_settings.FACEBOOK_STORE_FRIENDS:
            facebook.get_and_store_friends(user)
        transaction.savepoint_commit(sid)
    except IntegrityError, e:
        logger.warn(u'Integrity error encountered during registration, '
                'probably a double submission %s' % e,
            exc_info=sys.exc_info(), extra={
            'request': request,
            'data': {
                 'body': unicode(e),
             }
        })
        transaction.savepoint_rollback(sid)

    profile = user.get_profile()
    #store the access token for later usage if the profile model supports it
    if hasattr(profile, 'access_token'):
        # only update the access token if it is long lived or we are set to store all
        if not graph.expires or facebook_settings.FACEBOOK_STORE_ALL_ACCESS_TOKENS:
            # and not equal to the current token
            if graph.access_token != profile.access_token:
                profile.access_token = graph.access_token
                profile.save()
        
        #warn if we didn't get offline access
        if graph.expires:
            logger.warn('we shouldnt be finding a graph expiration, its set to %s', graph.expires)

    return action, user


def _login_user(request, facebook, authenticated_user, update=False):
    login(request, authenticated_user)

    if update:
        _connect_user(request, facebook)

    return authenticated_user


def _connect_user(request, facebook):
    '''
    Update the fields on the user model and connects it to the facebook account

    '''
    if not request.user.is_authenticated():
        raise ValueError(
            'Connect user can only be used on authenticated users')
    if not facebook.is_authenticated():
        raise ValueError(
            'Facebook needs to be authenticated for connect flows')

    user = _update_user(request.user, facebook)

    return user


def _register_user(request, facebook, profile_callback=None,
                   remove_old_connections=False):
    '''
    Creates a new user and authenticates
    The registration form handles the registration and validation
    Other data on the user profile is updates afterwards

    if remove_old_connections = True we will disconnect old
    profiles from their facebook flow
    '''
    if not facebook.is_authenticated():
        raise ValueError(
            'Facebook needs to be authenticated for connect flows')

    # get the backend on new registration systems, or none
    # if we are on an older version
    backend = get_registration_backend()

    # gets the form class specified in FACEBOOK_REGISTRATION_FORM
    form_class = get_form_class(backend, request)

    facebook_data = facebook.facebook_registration_data()

    data = request.POST.copy()
    for k, v in facebook_data.items():
        if not data.get(k):
            data[k] = v
    if remove_old_connections:
        _remove_old_connections(facebook_data['facebook_id'])

    if request.REQUEST.get('force_registration_hard'):
        data['email'] = data['email'].replace(
            '@', '+test%s@' % randint(0, 1000000000))

    form = form_class(data=data, files=request.FILES,
        initial={'ip': request.META['REMOTE_ADDR']})

    if not form.is_valid():
        error = facebook_exceptions.IncompleteProfileError('Facebook data %s '
            'gave error %s' % (facebook_data, form.errors))
        error.form = form
        raise error

    #for new registration systems use the backends methods of saving
    if backend:
        new_user = backend.register(request, **form.cleaned_data)
    else:
        # For backward compatibility, if django-registration form is used
        try:
            new_user = form.save(profile_callback=profile_callback)
        except TypeError:
            new_user = form.save()

    signals.facebook_user_registered.send(sender=auth.models.User,
        user=new_user, facebook_data=facebook_data)

    #update some extra data not yet done by the form
    new_user = _update_user(new_user, facebook)

    # IS this the correct way for django 1.3? seems to require the backend
    # attribute for some reason
    new_user.backend = 'django_facebook.auth_backends.FacebookBackend'
    auth.login(request, new_user)

    return new_user


def _remove_old_connections(facebook_id, current_user_id=None):
    '''
    Removes the facebook id for profiles with the specified facebook id
    which arent the current user id
    '''
    profile_class = get_profile_class()
    other_facebook_accounts = profile_class.objects.filter(
        facebook_id=facebook_id)
    if current_user_id:
        other_facebook_accounts = other_facebook_accounts.exclude(
            user__id=current_user_id)
    other_facebook_accounts.update(facebook_id=None)


def _update_user(user, facebook):
    '''
    Updates the user and his/her profile with the data from facebook
    '''
    # if you want to add fields to ur user model instead of the
    # profile thats fine
    # partial support (everything except raw_data and facebook_id is included)
    facebook_data = facebook.facebook_registration_data(username=False)
    facebook_fields = ['facebook_name', 'facebook_profile_url', 'gender',
        'date_of_birth', 'about_me', 'website_url', 'first_name', 'last_name']
    user_dirty = profile_dirty = False
    profile = user.get_profile()

    signals.facebook_pre_update.send(sender=get_profile_class(),
        profile=profile, facebook_data=facebook_data)

    profile_field_names = [f.name for f in profile._meta.fields]
    user_field_names = [f.name for f in user._meta.fields]

    #set the facebook id and make sure we are the only user with this id
    if facebook_data['facebook_id'] != profile.facebook_id:
        logger.info('profile facebook id changed from %s to %s',
                    repr(facebook_data['facebook_id']),
                    repr(profile.facebook_id))
        profile.facebook_id = facebook_data['facebook_id']
        profile_dirty = True
        _remove_old_connections(profile.facebook_id, user.id)

    #update all fields on both user and profile
    for f in facebook_fields:
        facebook_value = facebook_data.get(f, False)
        if facebook_value:
            if (f in profile_field_names and hasattr(profile, f) and
                not getattr(profile, f, False)):
                logger.debug('profile field %s changed from %s to %s', f,
                             getattr(profile, f), facebook_value)
                setattr(profile, f, facebook_value)
                profile_dirty = True
            elif (f in user_field_names and hasattr(user, f) and
                  not getattr(user, f, False)):
                logger.debug('user field %s changed from %s to %s', f,
                             getattr(user, f), facebook_value)
                setattr(user, f, facebook_value)
                user_dirty = True

    #write the raw data in case we missed something
    if hasattr(profile, 'raw_data'):
        serialized_fb_data = json.dumps(facebook.facebook_profile_data())
        if profile.raw_data != serialized_fb_data:
            logger.debug('profile raw data changed from %s to %s',
                         profile.raw_data, serialized_fb_data)
            profile.raw_data = serialized_fb_data
            profile_dirty = True

    #save both models if they changed
    if user_dirty:
        user.save()
    if profile_dirty:
        profile.save()

    signals.facebook_post_update.send(sender=get_profile_class(),
        profile=profile, facebook_data=facebook_data)

    return user

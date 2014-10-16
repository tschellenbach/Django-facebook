from django.contrib import auth
from django.contrib.auth import authenticate, login
from django.core.files.temp import NamedTemporaryFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import transaction
from django.db.utils import IntegrityError
import json
from django_facebook import exceptions as facebook_exceptions, \
    settings as facebook_settings, signals
from django_facebook.api import get_facebook_graph
from django_facebook.utils import get_registration_backend, get_form_class, \
    get_profile_model, to_bool, get_user_model, get_instance_for,\
    get_user_attribute, try_get_profile, get_model_for_attribute,\
    get_instance_for_attribute, update_user_attributes
from random import randint
import logging
import sys
import urllib
try:
    import urllib2
except ImportError:
    import urllib.error as urllib2


logger = logging.getLogger(__name__)


class CONNECT_ACTIONS:

    class LOGIN:
        pass

    class CONNECT(LOGIN):
        pass

    class REGISTER:
        pass


def connect_user(request, access_token=None, facebook_graph=None, connect_facebook=False):
    '''
    Given a request either

    - (if authenticated) connect the user
    - login
    - register
    '''
    user = None
    graph = facebook_graph or get_facebook_graph(request, access_token)

    converter = get_instance_for('user_conversion', graph)

    assert converter.is_authenticated()
    facebook_data = converter.facebook_profile_data()
    force_registration = request.REQUEST.get('force_registration') or\
        request.REQUEST.get('force_registration_hard')

    logger.debug('force registration is set to %s', force_registration)
    if connect_facebook and request.user.is_authenticated() and not force_registration:
        # we should only allow connect if users indicate they really want to connect
        # only when the request.CONNECT_FACEBOOK = 1
        # if this isn't present we just do a login
        action = CONNECT_ACTIONS.CONNECT
        # default behaviour is not to overwrite old data
        user = _connect_user(request, converter, overwrite=True)
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
            update = getattr(auth_user, 'fb_update_required', False)
            profile = try_get_profile(auth_user)
            current_facebook_id = get_user_attribute(
                auth_user, profile, 'facebook_id')
            if not current_facebook_id:
                update = True
            # login the user
            user = _login_user(request, converter, auth_user, update=update)
        else:
            action = CONNECT_ACTIONS.REGISTER
            # when force registration is active we should remove the old
            # profile
            try:
                user = _register_user(request, converter,
                                      remove_old_connections=force_registration)
            except facebook_exceptions.AlreadyRegistered as e:
                # in Multithreaded environments it's possible someone beats us to
                # the punch, in that case just login
                logger.info(
                    'parallel register encountered, slower thread is doing a login')
                auth_user = authenticate(
                    facebook_id=facebook_data['id'], **kwargs)
                if not auth_user:
                    # We don't have a valid user so raise
                    raise e
                action = CONNECT_ACTIONS.LOGIN
                user = _login_user(request, converter, auth_user, update=False)

    _update_likes_and_friends(request, user, converter)

    _update_access_token(user, graph)

    logger.info('connect finished with action %s', action)

    return action, user


def _login_user(request, facebook, authenticated_user, update=False):
    login(request, authenticated_user)

    if update:
        _connect_user(request, facebook)

    return authenticated_user


def _connect_user(request, facebook, overwrite=True):
    '''
    Update the fields on the user model and connects it to the facebook account

    '''
    if not request.user.is_authenticated():
        raise ValueError(
            'Connect user can only be used on authenticated users')
    if not facebook.is_authenticated():
        raise ValueError(
            'Facebook needs to be authenticated for connect flows')

    data = facebook.facebook_profile_data()
    facebook_id = data['id']

    # see if we already have profiles connected to this Facebook account
    old_connections = _get_old_connections(facebook_id, request.user.id)[:20]
    if old_connections and not request.REQUEST.get('confirm_connect'):
        raise facebook_exceptions.AlreadyConnectedError(list(old_connections))
    user = _update_user(request.user, facebook, overwrite=overwrite)

    return user


def _update_likes_and_friends(request, user, facebook):
    # store likes and friends if configured
    sid = transaction.savepoint()
    try:
        if facebook_settings.FACEBOOK_STORE_LIKES:
            facebook.get_and_store_likes(user)
        if facebook_settings.FACEBOOK_STORE_FRIENDS:
            facebook.get_and_store_friends(user)
        transaction.savepoint_commit(sid)
    except IntegrityError as e:
        logger.warn(u'Integrity error encountered during registration, '
                    'probably a double submission %s' % e,
                    exc_info=sys.exc_info(), extra={
                        'request': request,
                        'data': {
                            'body': unicode(e),
                        }
                    })
        transaction.savepoint_rollback(sid)


def _update_access_token(user, graph):
    '''
    Conditionally updates the access token in the database
    '''
    profile = try_get_profile(user)
    model_or_profile = get_instance_for_attribute(
        user, profile, 'access_token')
    # store the access token for later usage if the profile model supports it
    if model_or_profile:
        # update if not equal to the current token
        new_token = graph.access_token != model_or_profile.access_token
        token_message = 'a new' if new_token else 'the same'
        logger.info(
            'found %s token %s', token_message, graph.access_token[:10])
        if new_token:
            logger.info('access token changed, updating now')
            model_or_profile.update_access_token(graph.access_token)
            model_or_profile.save()
            # see if we can extend the access token
            # this runs in a task, after extending the token we fire an event
            model_or_profile.extend_access_token()


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
    logger.info('running backend %s for registration', backend)

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
        # show errors in sentry
        form_errors = form.errors
        error = facebook_exceptions.IncompleteProfileError(
            'Facebook signup incomplete')
        error.form = form
        raise error

    try:
        # for new registration systems use the backends methods of saving
        new_user = None
        if backend:
            new_user = backend.register(request,
                                        form=form, **form.cleaned_data)
        # fall back to the form approach
        if new_user is None:
            raise ValueError(
                'new_user is None, note that backward compatability for the older versions of django registration has been dropped.')
    except IntegrityError as e:
        # this happens when users click multiple times, the first request registers
        # the second one raises an error
        raise facebook_exceptions.AlreadyRegistered(e)

    # update some extra data not yet done by the form
    new_user = _update_user(new_user, facebook)

    signals.facebook_user_registered.send(sender=get_user_model(),
                                          user=new_user, facebook_data=facebook_data, request=request, converter=facebook)
    # IS this the correct way for django 1.3? seems to require the backend
    # attribute for some reason
    new_user.backend = 'django_facebook.auth_backends.FacebookBackend'
    auth.login(request, new_user)

    return new_user


def _get_old_connections(facebook_id, current_user_id=None):
    '''
    Gets other accounts connected to this facebook id, which are not
    attached to the current user
    '''
    user_or_profile_model = get_model_for_attribute('facebook_id')
    other_facebook_accounts = user_or_profile_model.objects.filter(
        facebook_id=facebook_id)
    kwargs = {}

    if current_user_id:
        # if statement since we need to support both
        user_model = get_user_model()
        if user_or_profile_model == user_model:
            kwargs['id'] = current_user_id
        else:
            kwargs['user'] = current_user_id
        other_facebook_accounts = other_facebook_accounts.exclude(**kwargs)
    return other_facebook_accounts


def _remove_old_connections(facebook_id, current_user_id=None):
    '''
    Removes the facebook id for profiles with the specified facebook id
    which arent the current user id
    '''
    other_facebook_accounts = _get_old_connections(
        facebook_id, current_user_id)
    other_facebook_accounts.update(facebook_id=None)


def _update_user(user, facebook, overwrite=True):
    '''
    Updates the user and his/her profile with the data from facebook
    '''
    # if you want to add fields to ur user model instead of the
    # profile thats fine
    # partial support (everything except raw_data and facebook_id is included)
    facebook_data = facebook.facebook_registration_data(username=False)
    facebook_fields = ['facebook_name', 'facebook_profile_url', 'gender',
                       'date_of_birth', 'about_me', 'website_url', 'first_name', 'last_name']

    profile = try_get_profile(user)
    # which attributes to update
    attributes_dict = {}

    # send the signal that we're updating
    signals.facebook_pre_update.send(sender=get_user_model(), user=user,
                                     profile=profile, facebook_data=facebook_data)

    # set the facebook id and make sure we are the only user with this id
    current_facebook_id = get_user_attribute(user, profile, 'facebook_id')
    facebook_id_changed = facebook_data['facebook_id'] != current_facebook_id
    overwrite_allowed = overwrite or not current_facebook_id

    # update the facebook id and access token
    facebook_id_overwritten = False
    if facebook_id_changed and overwrite_allowed:
        # when not overwriting we only update if there is no
        # profile.facebook_id
        logger.info('profile facebook id changed from %s to %s',
                    repr(facebook_data['facebook_id']),
                    repr(current_facebook_id))
        attributes_dict['facebook_id'] = facebook_data['facebook_id']
        facebook_id_overwritten = True

    if facebook_id_overwritten:
        _remove_old_connections(facebook_data['facebook_id'], user.id)

    # update all fields on both user and profile
    for f in facebook_fields:
        facebook_value = facebook_data.get(f, False)
        current_value = get_user_attribute(user, profile, f, None)
        if facebook_value and not current_value:
            attributes_dict[f] = facebook_value

    # write the raw data in case we missed something
    serialized_fb_data = json.dumps(facebook.facebook_profile_data())
    current_raw_data = get_user_attribute(user, profile, 'raw_data')
    if current_raw_data != serialized_fb_data:
        attributes_dict['raw_data'] = serialized_fb_data

    image_url = facebook_data['image']
    # update the image if we are allowed and have to
    if facebook_settings.FACEBOOK_STORE_LOCAL_IMAGE:
        image_field = get_user_attribute(user, profile, 'image', True)
        if not image_field:
            image_name, image_file = _update_image(
                facebook_data['facebook_id'], image_url)
            image_field.save(image_name, image_file)

    # save both models if they changed
    update_user_attributes(user, profile, attributes_dict)
    if getattr(user, '_fb_is_dirty', False):
        user.save()
    if getattr(profile, '_fb_is_dirty', False):
        profile.save()

    signals.facebook_post_update.send(sender=get_user_model(),
                                      user=user, profile=profile, facebook_data=facebook_data)

    return user


def _update_image(facebook_id, image_url):
    '''
    Updates the user profile's image to the given image url
    Unfortunately this is quite a pain to get right with Django
    Suggestions to improve this are welcome
    '''
    image_name = 'fb_image_%s.jpg' % facebook_id
    image_temp = NamedTemporaryFile()
    try:
        image_response = urllib2.urlopen(image_url)
    except AttributeError:
        image_response = urllib.request.urlopen(image_url)
    image_content = image_response.read()
    image_temp.write(image_content)
    http_message = image_response.info()
    image_size = len(image_content)
    try:
        content_type = http_message.type
    except AttributeError:
        content_type = http_message.get_content_type()
    image_file = InMemoryUploadedFile(
        file=image_temp, name=image_name, field_name='image',
        content_type=content_type, size=image_size, charset=None
    )
    image_file.seek(0)
    image_temp.flush()
    return image_name, image_file


def update_connection(request, graph):
    '''
    A special purpose view for updating the connection with an existing user
    - updates the access token (already done in get_graph)
    - sets the facebook_id if nothing is specified
    - stores friends and likes if possible
    '''
    converter = get_instance_for('user_conversion', graph)
    user = _connect_user(request, converter, overwrite=False)
    _update_likes_and_friends(request, user, converter)
    _update_access_token(user, graph)
    return user

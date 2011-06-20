from django.contrib import auth
from django.contrib.auth import authenticate, login
from django.utils import simplejson as json
from django_facebook import settings as facebook_settings
from django_facebook import exceptions as facebook_exceptions
from django_facebook.api import get_facebook_graph
from random import randint
import logging
from utils import get_profile_class
from django.db.utils import IntegrityError
import sys

logger = logging.getLogger(__name__)


class CONNECT_ACTIONS:
    class LOGIN: pass
    class CONNECT(LOGIN): pass
    class REGISTER: pass


def connect_user(request, access_token=None, facebook_graph=None):
    '''
    Given a request either
    
    - (if authenticated) connect the user
    - login
    - register
    '''
    #TODO, instead of using access_token this should probably accept a facebook_graph as well
    user = None
    facebook = facebook_graph or get_facebook_graph(request, access_token)
    assert facebook.is_authenticated()
    facebook_data = facebook.facebook_profile_data()
    force_registration = request.REQUEST.get('force_registration') or request.REQUEST.get('force_registration_hard')
    
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
        authenticated_user = authenticate(facebook_id=facebook_data['id'], **kwargs)
        if authenticated_user and not force_registration:
            action = CONNECT_ACTIONS.LOGIN

            ## Has the user registered without Facebook, using the verified FB email address?
            # It is after all quite common to use email addresses for usernames
            if not authenticated_user.get_profile().facebook_id:
                update = True
            else:
                update = getattr(authenticated_user, 'fb_update_required', False)
            user = _login_user(request, facebook, authenticated_user, update=update)
        else:
            action = CONNECT_ACTIONS.REGISTER
            user = _register_user(request, facebook)
            
    #store likes and friends if configured
    try:
        if facebook_settings.FACEBOOK_STORE_LIKES:
            facebook.store_likes(user)
        if facebook_settings.FACEBOOK_STORE_FRIENDS:
            facebook.store_friends(user)
    except IntegrityError, e:
        logger.warn(u'Integrity error encountered during registration, probably a double submission %s' % e, 
            exc_info=sys.exc_info(), extra={
            'request': request,
            'data': {
                 'body': unicode(e),
             }
        })
            
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
        raise ValueError, 'Connect user can only be used on authenticated users'
    if not facebook.is_authenticated():
        raise ValueError, 'Facebook needs to be authenticated for connect flows'
    
    user = _update_user(request.user, facebook)

    return user


def _register_user(request, facebook, profile_callback=None):
    '''
    Creates a new user and authenticates
    The registration form handles the registration and validation
    Other data on the user profile is updates afterwards
    '''
    if not facebook.is_authenticated():
        raise ValueError, 'Facebook needs to be authenticated for connect flows'
    
    from registration.forms import RegistrationFormUniqueEmail
    import registration
    
    new_reg_module = True
    try:        
        from registration.backends import get_backend
    except ImportError, e:
        new_reg_module = False
        
    form_class = RegistrationFormUniqueEmail
    facebook_data = facebook.facebook_registration_data()

    data = request.POST.copy()
    for k, v in facebook_data.items():
        if not data.get(k):
            data[k] = v
    
    if request.REQUEST.get('force_registration_hard'):
        data['email'] = data['email'].replace('@', '+%s@' % randint(0, 100000))

    form = form_class(data=data, files=request.FILES,
        initial={'ip': request.META['REMOTE_ADDR']})

    if not form.is_valid():
        error = facebook_exceptions.IncompleteProfileError('Facebook data %s gave error %s' % (facebook_data, form.errors))
        error.form = form
        raise error

    if new_reg_module:
        #support for the newer implementation
        try:
            from django.conf import settings
            backend = get_backend(settings.REGISTRATION_BACKEND)
        except:
            raise ValueError, 'Cannot get django-registration backend from settings.REGISTRATION_BACKEND'
        new_user = backend.register(request, **form.cleaned_data)
    else:
        new_user = form.save(profile_callback=profile_callback)
    
    #update some extra data not yet done by the form
    new_user = _update_user(new_user, facebook)
        
    #IS this the correct way for django 1.3? seems to require the backend attribute for some reason
    new_user.backend = 'django_facebook.auth_backends.FacebookBackend'
    auth.login(request, new_user)
    
    return new_user


def _update_user(user, facebook):
    '''
    Updates the user and his/her profile with the data from facebook
    '''
    #if you want to add fields to ur user model instead of the profile thats fine
    #partial support (everything except raw_data and facebook_id is included)
    facebook_data = facebook.facebook_registration_data()
    facebook_fields = ['facebook_name', 'facebook_profile_url', 'date_of_birth', 'about_me', 'website_url', 'first_name', 'last_name']
    user_dirty = profile_dirty = False
    profile = user.get_profile()
    profile_field_names = [f.name for f in profile._meta.fields]
    user_field_names = [f.name for f in user._meta.fields]
    
    #set the facebook id and make sure we are the only user with this id
    if facebook_data['facebook_id'] != profile.facebook_id:
        profile.facebook_id = facebook_data['facebook_id']
        profile_dirty = True
        #like i said, me and only me
        profile_class = get_profile_class()
        profile_class.objects.filter(facebook_id=profile.facebook_id).exclude(user__id=user.id).update(facebook_id=None)

    #update all fields on both user and profile
    for f in facebook_fields:
        facebook_value = facebook_data.get(f, False)
        if facebook_value:
            if f in profile_field_names and not getattr(profile, f, False):
                setattr(profile, f, facebook_value)
                profile_dirty = True
            elif f in user_field_names and not getattr(user, f, False):
                setattr(user, f, facebook_value)
                user_dirty = True

    #write the raw data in case we missed something
    if hasattr(profile, 'raw_data'):
        serialized_fb_data = json.dumps(facebook.facebook_profile_data())
        profile.raw_data = serialized_fb_data
        profile_dirty = True
        
    #save both models if they changed
    if user_dirty:
        user.save()
    if profile_dirty:
        profile.save()
        
    return user



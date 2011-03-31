from django.contrib import auth
from django.contrib.auth import authenticate, login
from django_facebook import exceptions as facebook_exceptions
from django_facebook.api import get_facebook_graph
from random import randint
import logging
from django.utils import simplejson as json

logger = logging.getLogger(__name__)


class CONNECT_ACTIONS:
    class LOGIN: pass
    class CONNECT(LOGIN): pass
    class REGISTER: pass


def connect_user(request, access_token=None):
    '''
    Given a request either
    
    - (if authenticated) connect the user
    - login
    - register
    '''
    user = None
    facebook = get_facebook_graph(request, access_token)
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
            user = _login_user(request, facebook, authenticated_user, update=getattr(authenticated_user, 'fb_update_required', False))
        else:
            action = CONNECT_ACTIONS.REGISTER
            user = _register_user(request, facebook)
            
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
    
    facebook_data = facebook.facebook_registration_data()
    profile = request.user.get_profile()
    user = request.user
    #update the fields in the profile
    profile_fields = profile._meta.fields
    user_fields = user._meta.fields
    profile_field_names = [f.name for f in profile_fields]
    user_field_names = [f.name for f in user_fields]
    facebook_fields = ['facebook_name', 'facebook_profile_url', 'date_of_birth', 'about_me', 'facebook_id', 'website_url', 'first_name', 'last_name']

    for f in facebook_fields:
        facebook_value = facebook_data.get(f, False)
        if facebook_value:
            if f in profile_field_names and not getattr(profile, f, False):
                setattr(profile, f, facebook_value)
            elif f in user_field_names and not getattr(user, f, False):
                setattr(user, f, facebook_value)

    if hasattr(profile, 'raw_data'):
        serialized_fb_data = json.dumps(facebook.facebook_profile_data())
        profile.raw_data = serialized_fb_data

    profile.save()
    user.save()

    return user


def _register_user(request, facebook, profile_callback=None):
    if not facebook.is_authenticated():
        raise ValueError, 'Facebook needs to be authenticated for connect flows'
    
    from registration.forms import RegistrationFormUniqueEmail
    import registration
    new_reg_module = hasattr(registration, 'backends')
    
    if new_reg_module:
        from registration.backends import get_backend
        
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
    profile = new_user.get_profile()
    if hasattr(profile, 'raw_data'):
        serialized_fb_data = json.dumps(facebook.facebook_profile_data())
        profile.raw_data = serialized_fb_data
        profile.save()
        
    auth.login(request, new_user)
    
    
    

    return new_user



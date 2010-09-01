from django.contrib.auth import authenticate, login
from django.contrib import auth
from django.http import HttpResponseRedirect
from django_facebook.utils import next_redirect
from django_facebook.view_decorators import fashiolista_env


@fashiolista_env
def connect(request):
    '''
    Connect a user if it is authenticated
    
    Else
        Login or registers the given facebook user
        Redirects to a registration form if the data is invalid or incomplete
    '''
    facebook_login = bool(int(request.REQUEST.get('facebook_login', 0)))
    if facebook_login:
        facebook = request.facebook()
        if facebook.is_authenticated():
            profile = facebook.facebook_profile_data()
            if request.user.is_authenticated():
                return _connect_user(request, facebook)
            else:
                kwargs = {}
                email = profile.get('email', False)
                email_verified = profile.get('verified', False)
                if email and email_verified:
                    kwargs = {'facebook_email': email}
                authenticated_user = authenticate(facebook_id=profile['id'], **kwargs)
                if authenticated_user:
                    return _login_user(request, facebook, authenticated_user, update=getattr(authenticated_user, 'fb_update_required', False))
                else:
                    return _register_user(request, facebook, authenticated_user)
        else:
            return next_redirect(request)


def _connect_user(request, facebook):
    if not request.user.is_authenticated():
        raise ValueError, 'Connect user can only be used on authenticated users'
    if facebook.is_authenticated():
        facebook_data = facebook.facebook_registration_data()
        request.notifications.success("You have connected your account to %s's facebook profile" % facebook_data['name'])
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

        profile.save()
        user.save()

    return next_redirect(request)


def _login_user(request, facebook, authenticated_user, update=False):
    login(request, authenticated_user)

    if update:
        _connect_user(request, facebook)

    return next_redirect(request)


def _register_user(request, facebook, authenticated_user, profile_callback=None):
    request.template = 'registration/registration_form.html'
    request.context['facebook_mode'] = True
    facebook_data = {}
    from registration.forms import RegistrationFormUniqueEmail
    form_class = RegistrationFormUniqueEmail
    if facebook.is_authenticated():
        request.context['facebook_data'] = facebook_data = facebook.facebook_registration_data()

    if request.method == 'POST':
        data = request.POST.copy()
        for k, v in facebook_data.items():
            if not data.get(k):
                data[k] = v

        form = form_class(data=data, files=request.FILES,
            initial={'ip': request.META['REMOTE_ADDR']})

        if form.is_valid():
            new_user = form.save(profile_callback=profile_callback)
            auth.login(request, new_user)
            member_overview_url = new_user.get_profile().url['overview']
            return HttpResponseRedirect(member_overview_url)
    else:
        initial = facebook_data.copy()
        initial.update(request.GET.items())
        form = form_class(initial=initial)

    request.context['form'] = form



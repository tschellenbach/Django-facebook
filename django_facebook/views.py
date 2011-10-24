import logging
import sys

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect, QueryDict
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt

# NOTE: from inside the application, you can directly import the file
from django_facebook import exceptions as facebook_exceptions, \
    settings as facebook_settings
from django_facebook.api import get_facebook_graph, get_persistent_graph,\
    FacebookUserConverter
from django_facebook.canvas import generate_oauth_url
from django_facebook.connect import CONNECT_ACTIONS, connect_user
from django_facebook.utils import next_redirect
from django_facebook.decorators import facebook_required

logger = logging.getLogger(__name__)



@facebook_required(scope='publish_stream')
def wall_post(request):
    fb = get_persistent_graph(request)

    message = request.REQUEST.get('message')
    fb.set('me/feed', message=message)

    messages.info(request, 'Posted the message to your wall')

    return next_redirect(request)


@facebook_required(scope='publish_stream,user_photos')
def image_upload(request):
    fb = get_persistent_graph(request)
    pictures = request.REQUEST.getlist('pictures')

    for picture in pictures:
        fb.set('me/photos', url=picture, message='the writing is one The '
            'wall image %s' % picture)

    messages.info(request, 'The images have been added to your profile!')

    return next_redirect(request)

@csrf_exempt
def connect(request):
    '''
    Handles the view logic around connect user
    - (if authenticated) connect the user
    - login
    - register
    '''
    context = RequestContext(request)

    assert context.get('FACEBOOK_APP_ID'), 'Please specify a facebook app id '\
        'and ensure the context processor is enabled'
    facebook_login = bool(int(request.REQUEST.get('facebook_login', 0)))

    if facebook_login:
        graph = get_facebook_graph(request)
        if graph:
            facebook = FacebookUserConverter(graph)
            if facebook.is_authenticated():
                facebook_data = facebook.facebook_profile_data()
                #either, login register or connect the user
                try:
                    action, user = connect_user(request)
                except facebook_exceptions.IncompleteProfileError, e:
                    warn_message = u'Incomplete profile data encountered '\
                        'with error %s' % e
                    logger.warn(warn_message,
                        exc_info=sys.exc_info(), extra={
                        'request': request,
                        'data': {
                             'username': request.user.username,
                             'facebook_data': facebook.facebook_profile_data(),
                             'body': unicode(e),
                         }
                    })

                    context['facebook_mode'] = True
                    context['form'] = e.form
                    return render_to_response(
                        'registration/registration_form.html',
                        context_instance=context,
                    )

                if action is CONNECT_ACTIONS.CONNECT:
                    messages.info(request, _("You have connected your account "
                        "to %s's facebook profile") % facebook_data['name'])
                elif action is CONNECT_ACTIONS.REGISTER:
                    return user.get_profile().post_facebook_registration(request)
        else:
            return next_redirect(request, next_key=['error_next', 'next'],
                additional_params=dict(fb_error_or_cancel=1))

        return next_redirect(request)

    if not settings.DEBUG and facebook_settings.FACEBOOK_HIDE_CONNECT_TEST:
        raise Http404

    return render_to_response('django_facebook/connect.html', context)








@csrf_exempt
def canvas(request):
    context = RequestContext(request)

    context['auth_url'] = generate_oauth_url()
    fb = get_persistent_graph(request)
    if fb.is_authenticated():
        likes = context['facebook'].get_connections("me", "likes", limit=3)
        logger.info('found these likes %s', likes)

    return render_to_response('django_facebook/canvas.html', context)


@csrf_exempt
def my_style(request):
    context = RequestContext(request)
    context['auth_url'] = generate_oauth_url()

    return render_to_response('django_facebook/my_style.html', context)

import logging

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt

# NOTE: from inside the application, you can directly import the file
from django_facebook import exceptions as facebook_exceptions, \
    settings as facebook_settings
from django_facebook.api import get_persistent_graph, FacebookUserConverter, \
    require_persistent_graph
from django_facebook.connect import CONNECT_ACTIONS, connect_user
from django_facebook.utils import next_redirect, get_registration_backend,\
    replication_safe, to_bool, error_next_redirect
from django_facebook.decorators import (facebook_required,
                                        facebook_required_lazy)
from open_facebook.utils import send_warning
from open_facebook import exceptions as open_facebook_exceptions
from django.shortcuts import redirect
from ssl import SSLError
from urllib2 import URLError
from django_facebook.models import OpenGraphShare


logger = logging.getLogger(__name__)


@facebook_required(scope='publish_actions')
def open_graph_beta(request):
    '''
    Simple example on how to do open graph postings
    '''
    fb = get_persistent_graph(request)
    entity_url = 'http://www.fashiolista.com/item/2081202/'
    fb.set('me/fashiolista:love', item=entity_url)
    messages.info(request,
                  'Frictionless sharing to open graph beta action '
                  'fashiolista:love with item_url %s, this url contains '
                  'open graph data which Facebook scrapes' % entity_url)


@facebook_required(scope='publish_actions')
def remove_og_share(request):
    graph = get_persistent_graph(request)
    og_share_id = request.GET.get('og_share_id')
    shares = OpenGraphShare.objects.filter(id=og_share_id)
    for share in shares:
        share.remove(graph)


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
@facebook_required_lazy(extra_params=dict(facebook_login='1'))
def connect(request):
    '''
    Exception and validation functionality around the _connect view
    Separated this out from _connect to preserve readability
    Don't bother reading this code, skip to _connect for the bit you're interested in :)
    '''
    facebook_login = to_bool(request.REQUEST.get('facebook_login'))
    context = RequestContext(request)

    #validation to ensure the context processor is enabled
    if not context.get('FACEBOOK_APP_ID'):
        message = 'Please specify a Facebook app id and ensure the context processor is enabled'
        raise ValueError(message)

    #hide the connect page, convenient for testing with new users in production though
    if not facebook_login and not settings.DEBUG and facebook_settings.FACEBOOK_HIDE_CONNECT_TEST:
        raise Http404('not showing the connect page')

    try:
        response = _connect(request, facebook_login)
    except open_facebook_exceptions.FacebookUnreachable, e:
        #often triggered when Facebook is slow
        warning_format = u'%s, often caused by Facebook slowdown, error %s'
        warn_message = warning_format % (type(e), e.message)
        send_warning(warn_message, e=e)
        response = error_next_redirect(request,
                                       additional_params=dict(
                                           fb_error_or_cancel=1)
                                       )

    return response


def _connect(request, facebook_login):
    '''
    Handles the view logic around connect user
    - (if authenticated) connect the user
    - login
    - register
    '''
    backend = get_registration_backend()
    context = RequestContext(request)

    if facebook_login:
        logger.info('trying to connect using Facebook')
        graph = require_persistent_graph(request)
        authenticated = False
        if graph:
            logger.info('found a graph object')
            facebook = FacebookUserConverter(graph)
            authenticated = facebook.is_authenticated()

            if authenticated:
                logger.info('Facebook is authenticated')
                facebook_data = facebook.facebook_profile_data()
                #either, login register or connect the user
                try:
                    action, user = connect_user(request)
                    logger.info('Django facebook performed action: %s', action)
                except facebook_exceptions.IncompleteProfileError, e:
                    #show them a registration form to add additional data
                    warning_format = u'Incomplete profile data encountered with error %s'
                    warn_message = warning_format % e.message
                    send_warning(warn_message, e=e,
                                 facebook_data=facebook_data)

                    context['facebook_mode'] = True
                    context['form'] = e.form
                    return render_to_response(
                        facebook_settings.FACEBOOK_REGISTRATION_TEMPLATE,
                        context_instance=context,
                    )
                except facebook_exceptions.AlreadyConnectedError, e:
                    user_ids = [u.user_id for u in e.users]
                    ids_string = ','.join(map(str, user_ids))
                    return error_next_redirect(
                        request,
                        additional_params=dict(already_connected=ids_string))

                if action is CONNECT_ACTIONS.CONNECT:
                    #connect means an existing account was attached to facebook
                    messages.info(request, _("You have connected your account "
                                             "to %s's facebook profile") % facebook_data['name'])
                elif action is CONNECT_ACTIONS.REGISTER:
                    #hook for tying in specific post registration functionality
                    response = backend.post_registration_redirect(
                        request, user)
                    #compatibility for Django registration backends which return redirect tuples instead of a response
                    if not isinstance(response, HttpResponse):
                        to, args, kwargs = response
                        response = redirect(to, *args, **kwargs)
                    return response

        #either redirect to error next or raise an error (caught by the decorator and going into a retry
        if not authenticated:
            if 'attempt' in request.GET:
                return error_next_redirect(request, additional_params=dict(fb_error_or_cancel=1))
            else:
                logger.info('Facebook authentication needed for connect, '
                            'raising an error')
                raise open_facebook_exceptions.OpenFacebookException(
                    'please authenticate')

        #for CONNECT and LOGIN we simple redirect to the next page
        return next_redirect(request, default=facebook_settings.FACEBOOK_LOGIN_DEFAULT_REDIRECT)

    return render_to_response('django_facebook/connect.html', context)


def disconnect(request):
    '''
    Removes Facebook from the users profile
    And redirects to the specified next page
    '''
    if request.method == 'POST':
        messages.info(
            request, _("You have disconnected your Facebook profile."))
        profile = request.user.get_profile()
        profile.disconnect_facebook()
        profile.save()
    response = next_redirect(request)
    return response


@facebook_required_lazy(canvas=True)
def canvas(request):
    '''
    Example of a canvas page.
    Canvas pages require redirects to work using javascript instead of http headers
    The facebook required and facebook required lazy decorator abstract this away
    '''
    context = RequestContext(request)
    fb = require_persistent_graph(request)
    likes = fb.get('me/likes')['data']
    context['likes'] = likes

    return render_to_response('django_facebook/canvas.html', context)

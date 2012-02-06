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
from django_facebook.canvas import generate_oauth_url
from django_facebook.connect import CONNECT_ACTIONS, connect_user
from django_facebook.utils import next_redirect
from django_facebook.decorators import (facebook_required,
                                        facebook_required_lazy)
from open_facebook.utils import send_warning
from open_facebook.exceptions import OpenFacebookException


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
                  'Frictionless sharing to open graph beta action ' \
                  'fashiolista:love with item_url %s, this url contains ' \
                  'open graph data which Facebook scrapes' % entity_url)


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
        logger.info('trying to connect using facebook')
        graph = get_persistent_graph(request)
        if graph:
            logger.info('found a graph object')
            facebook = FacebookUserConverter(graph)
            if facebook.is_authenticated():
                logger.info('facebook is authenticated')
                facebook_data = facebook.facebook_profile_data()
                #either, login register or connect the user
                try:
                    action, user = connect_user(request)
                    logger.info('Django facebook performed action: %s', action)
                except facebook_exceptions.IncompleteProfileError, e:
                    warn_message = u'Incomplete profile data encountered '\
                        u'with error %s' % e
                    send_warning(warn_message, e=e,
                                 facebook_data=facebook_data)

                    context['facebook_mode'] = True
                    context['form'] = e.form
                    return render_to_response(
                        facebook_settings.FACEBOOK_REGISTRATION_TEMPLATE,
                        context_instance=context,
                    )

                if action is CONNECT_ACTIONS.CONNECT:
                    messages.info(request, _("You have connected your account "
                        "to %s's facebook profile") % facebook_data['name'])
                elif action is CONNECT_ACTIONS.REGISTER:
                    return user.get_profile().post_facebook_registration(
                        request)
        else:
            if 'attempt' in request.GET:
                return next_redirect(request, next_key=['error_next', 'next'],
                    additional_params=dict(fb_error_or_cancel=1))
            else:
                logger.info('Facebook authentication needed for connect, ' \
                            'raising an error')
                raise OpenFacebookException('please authenticate')

        return next_redirect(request)

    if not settings.DEBUG and facebook_settings.FACEBOOK_HIDE_CONNECT_TEST:
        raise Http404

    return render_to_response('django_facebook/connect.html', context)


def connect_async_ajax(request):
    '''
    Not yet implemented:
    The idea is to run the entire connect flow on the background using celery
    Freeing up webserver resources, when facebook has issues
    '''
    from django_facebook import tasks as facebook_tasks
    graph = get_persistent_graph(request)
    output = {}
    if graph:
        FacebookUserConverter(graph)
        task = facebook_tasks.async_connect_user(request, graph)
        output['task_id'] = task.id
    from open_facebook.utils import json
    json_dump = json.dumps(output)
    return HttpResponse(json_dump)


def poll_connect_task(request, task_id):
    '''
    Not yet implemented
    '''
    pass


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

@facebook_required_lazy(canvas=True)
def page_tab(request):
    '''
    Example of a canvas page.
    Canvas pages require redirects to work using javascript instead of http headers
    The facebook required and facebook required lazy decorator abstract this away
    '''
    context = RequestContext(request)
    facebook = require_persistent_graph(request)
    likes = facebook.get('me/likes')['data']
    context['likes'] = likes
    from user.models import FacebookPageTab
    
    signed_request = request.REQUEST.get('signed_request')
    
    data = facebook.prefetched_data
    page_id = data['page']['id']
    defaults = dict(created_by_user=data['user_id'])
    tab, created = FacebookPageTab.objects.get_or_create(page_id=page_id, defaults=defaults)
    context['facebook'] = facebook
    
    raise Exception, tab

    return render_to_response('django_facebook/page_tab.html', context)





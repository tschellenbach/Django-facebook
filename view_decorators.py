import cjson
from django import shortcuts as django_shortcuts
from django import http
from django.template import RequestContext
from django.contrib.auth import decorators
from functools import partial
from django_facebook import settings as facebook_settings



__all__ = ['content_admin_env']

class ViewError(Exception):
    pass

class UnknownViewResponseError(ViewError):
    pass

REQUEST_PROPERTIES = {
    'redirect': http.HttpResponseRedirect,
    'permanent_redirect': http.HttpResponsePermanentRedirect,
}


def _prepare_request(request, name):
    '''Add context and extra methods to the request'''
    request.context = RequestContext(request)
    request.context['tab'] = name

    for k, v in REQUEST_PROPERTIES.iteritems():
        setattr(request, k, v)

    return request


def _process_response(request, response):
    '''Generic response processing function, always returns HttpResponse'''

    '''If we add something to the context stack, pop it after adding'''
    pop = False
    try:
        if isinstance(response, dict):
            if request.is_ajax():
                return http.HttpResponse(cjson.encode(response),
                    mimetype='application/json')
            else:
                '''Add the dictionary to the context and let render_to_response
                handle it'''
                request.context.update(response)
                response = None
                pop = True

        if isinstance(response, http.HttpResponse):
            return response


        elif isinstance(response, basestring):
            if request.is_ajax():
                return http.HttpResponse(response, mimetype='application/json')
            else:
                return http.HttpResponse(response)

        elif response is None:
            if request.jinja:
                from coffin import shortcuts as jinja_shortcuts
                render_to_response = jinja_shortcuts.render_to_response
            else:
                render_to_response = django_shortcuts.render_to_response

            return render_to_response(request.template,
                context_instance=request.context)

        else:
            raise UnknownViewResponseError(
                '"%s" is an unsupported response type' % type(response))
    finally:
        if pop:
            request.context.pop()


def fashiolista_env(function=None, login_required=False):
    '''
    View decorator that automatically adds context and renders response

    Keyword arguments:
    login_required -- is everyone allowed or only authenticated users

    Adds a RequestContext (request.context) with the following context items:
    name -- current function name

    Stores the template in request.template and assumes it to be in
    <url>.html
    '''
    def _facebook(request, data_source=False):
        '''
        facebook_user = request.facebook_user()
        graph = facebook.GraphAPI(user["access_token"])
        profile = graph.get_object("me")
        friends = graph.get_connections("me", "friends")
        '''
        from django_facebook.facebook_api import FacebookAPI
        from django_facebook import facebook
        if not data_source:
            data_source = request.COOKIES

        user = facebook.get_user_from_cookie(data_source, facebook_settings.FACEBOOK_APP_ID, facebook_settings.FACEBOOK_APP_SECRET)
        facebook_connection = FacebookAPI(user)

        return facebook_connection


    def _env(request, *args, **kwargs):
        request.ajax = bool(int(request.REQUEST.get('ajax', 0)))
        request.context = None
        request.jinja = facebook_settings.FACEBOOK_JINJA
        request.facebook = partial(_facebook, request)
        try:
            name = function.__name__
            app = function.__module__.split('.')[0]

            request = _prepare_request(request, name)

            if app:
                request.template = '%s/%s.html' % (app, name)
            else:
                request.template = '%s.html' % name

            response = function(request, *args, **kwargs)



            return _process_response(request, response)
        finally:
            '''Remove the context reference from request to prevent leaking'''
            try:
                del request.context, request.template
                for k, v in REQUEST_PROPERTIES.iteritems():
                    delattr(request, k)
            except AttributeError:
                pass

    if function:
        _env.__name__ = function.__name__
        _env.__doc__ = function.__doc__
        _env.__dict__ = function.__dict__

        if login_required:
            return decorators.login_required(_env)
        else:
            return _env
    else:
        return lambda f: fashiolista_env(f, login_required)




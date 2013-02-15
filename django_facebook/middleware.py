# -*- coding: UTF-8 -*-
'''
Created on Jan 9, 2013

@author: dudu
'''
from urlparse import urlparse
from open_facebook.api import FacebookAuthorization, OpenFacebook
from django_facebook.canvas import generate_oauth_url
from django_facebook.utils import CanvasRedirect
from django_facebook.connect import connect_user
from django.contrib.auth import logout
from django_facebook import settings

redirect_login_oauth = CanvasRedirect(redirect_to=generate_oauth_url(),
                                      show_body=False)


class FacebookCanvasMiddleWare(object):

    def process_request(self, request):
        """
        check if referer is facebook. If yes, this is the canvas page:
        if not return.
        if yes:
        1) look for error. if error=permission denied -> redirect to permission. if other error: check what it can be
        2) get signed_request and parse it.
        3) if user_id and access_token not it parsed data -> redirect to permission page
        4) check permissions
        5) user:
        a) if user is authenticated: check if it's the same
        b) user is not authenticated: connect
        """
        #check referer to see if this is the first access
        #or it's part of navigation in app
        #facebook always sends a POST reuqest
        referer = request.META.get('HTTP_REFERER', None)
        if referer:
            urlparsed = urlparse(referer)
            if not urlparsed.netloc.endswith('facebook.com'):
                return
            #when there is an error, we attempt to allow user to reauthenticate
            if 'error' in request.GET:
                return redirect_login_oauth
        else:
            return

        #get signed_request
        signed_request = request.POST.get('signed_request', None)
        #not sure if this can happen, but better check anyway
        if not signed_request:
            return redirect_login_oauth

        #get signed_request and redirect to authorization dialog if app not authorized by user
        parsed_signed_request = FacebookAuthorization.parse_signed_data(
            signed_request)
        if 'user_id' not in parsed_signed_request or 'oauth_token' not in parsed_signed_request:
            return redirect_login_oauth

        access_token = parsed_signed_request['oauth_token']
        facebook_id = long(parsed_signed_request['user_id'])
        #check for permissions
        graph = OpenFacebook(access_token)
        permissions = set(graph.permissions())
        scope_list = set(settings.FACEBOOK_DEFAULT_SCOPE)
        if scope_list - permissions:
            return redirect_login_oauth
        #check if user authenticated and if it's the same
        if request.user.is_authenticated():
            try:
                current_user = request.user.get_profile()
            except:
                current_facebook_id = None
            else:
                current_facebook_id = current_user.facebook_id
            if not current_facebook_id or current_facebook_id != facebook_id:
                logout(request)
                #clear possible caches
                if hasattr(request, 'facebook'):
                    del request.facebook
                if request.session.get('graph', None):
                    del request.session['graph']
            else:
                #save last access_token to make sure we always have the most recent one
                current_user.access_token = access_token
                current_user.save()
        request.facebook = graph
        if not request.user.is_authenticated():
            _action, _user = connect_user(request, access_token, graph)
        #override http method, since this actually is a GET
        if request.method == 'POST':
            request.method = 'GET'
        return

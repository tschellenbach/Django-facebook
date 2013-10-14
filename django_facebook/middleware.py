# -*- coding: utf-8 -*-

from urlparse import urlparse

from django.contrib.auth import logout

from open_facebook.api import FacebookAuthorization, OpenFacebook

from django_facebook import settings
from django_facebook.canvas import generate_oauth_url
from django_facebook.connect import connect_user
from django_facebook.exceptions import MissingPermissionsError
from django_facebook.utils import ScriptRedirect


class FacebookCanvasMiddleWare(object):

    def process_request(self, request):
        """
        This middleware authenticates the facebook user when
        he/she is accessing the app from facebook (not an internal page)
        The flow is show below:

        if referer is facebook:
            it's a canvas app and the first hit on the app
            If error:
                attempt to reauthenticate using authorization dialog
            if signed_request not sent or does not have the user_id and the access_token:
                user has not authorized app
                redirect to authorization dialog
            else:
                check permissions
                if user is authenticated (in django):
                    check if current facebook user is the same that is authenticated
                    if not: logout authenticated user
                if user is not authenticated:
                    connect_user (django_facebook.connect module)
                changed method to GET. Facebook always sends a POST first.
        else:
            It's an internal page.
            No signed_request is sent.
            Return
        """

        # This call cannot be global'ized or Django will return an empty response
        # after the first one
        redirect_login_oauth = ScriptRedirect(redirect_to=generate_oauth_url(),
                                              show_body=False)
        # check referer to see if this is the first access
        # or it's part of navigation in app
        # facebook always sends a POST reuqest
        referer = request.META.get('HTTP_REFERER', None)
        if referer:
            urlparsed = urlparse(referer)
            is_facebook = urlparsed.netloc.endswith('facebook.com')
            # facebook redirect
            if is_facebook and urlparsed.path.endswith('/l.php'):
                return
            if not is_facebook:
                return
            # when there is an error, we attempt to allow user to
            # reauthenticate
            if 'error' in request.GET:
                return redirect_login_oauth
        else:
            return

        # get signed_request
        signed_request = request.POST.get('signed_request', None)
        try:
            # get signed_request
            parsed_signed_request = FacebookAuthorization.parse_signed_data(
                signed_request)
            access_token = parsed_signed_request['oauth_token']
            facebook_id = long(parsed_signed_request['user_id'])
        except:
            # redirect to authorization dialog
            # if app not authorized by user
            return redirect_login_oauth
        # check for permissions
        try:
            graph = self.check_permissions(access_token)
        except MissingPermissionsError:
            return redirect_login_oauth
        # check if user authenticated and if it's the same
        if request.user.is_authenticated():
            self.check_django_facebook_user(request, facebook_id, access_token)
        request.facebook = graph
        if not request.user.is_authenticated():
            _action, _user = connect_user(request, access_token, graph)
        # override http method, since this actually is a GET
        if request.method == 'POST':
            request.method = 'GET'
        return

    def check_permissions(self, access_token):
        graph = OpenFacebook(access_token)
        permissions = set(graph.permissions())
        scope_list = set(settings.FACEBOOK_DEFAULT_SCOPE)
        missing_perms = scope_list - permissions
        if missing_perms:
            permissions_string = ', '.join(missing_perms)
            error_format = 'Permissions Missing: %s'
            raise MissingPermissionsError(error_format % permissions_string)

        return graph

    def check_django_facebook_user(self, request, facebook_id, access_token):
        try:
            current_user = request.user.get_profile()
        except:
            current_facebook_id = None
        else:
            current_facebook_id = current_user.facebook_id
        if not current_facebook_id or current_facebook_id != facebook_id:
            logout(request)
            # clear possible caches
            if hasattr(request, 'facebook'):
                del request.facebook
            if request.session.get('graph', None):
                del request.session['graph']
        else:
            # save last access_token to make sure we always have the most
            # recent one
            current_user.access_token = access_token
            current_user.save()

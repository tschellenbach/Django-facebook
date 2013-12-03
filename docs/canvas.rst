
Canvas Application
------------------

In order to use build a facebook canvas application, you should add this to your ``MIDDLEWARE_CLASSES`` setting::

    'django_facebook.middleware.FacebookCanvasMiddleWare'

This middleware will check for the signed_request parameter in the url and take the appropriate action:
    * redirect to app authorization dialog if user has not authorized the app, some permission is missing or any other error.
    * login the current facebook user in django's system and store the access token.

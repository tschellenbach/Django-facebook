
Mobile usage
------------

You can get an access token by using the native Facebook SDK. Subsequently send this token to your Django based API.
In the view you can use the token to get a user.

.. code-block:: python

    from django_facebook.connect import connect_user
    access_token = request.POST['access_token']
    action, user = connect_user(request, access_token)
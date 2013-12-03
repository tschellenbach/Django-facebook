Getting a graph object
======================


Now that you have Django Facebook up and running you'll want to make API calls to Facebook.
The first step is getting an :class:`.OpenFacebook` object setup.


**User object**

For users which registered through Django Facebook, you'll have an access token stored in the database.
Note that by default tokens expire quickly (couple of hours), Django Facebook will try to extend these to 60 days.

.. code-block:: python

    graph = user.get_offline_graph()


**From the request**

If you've just authenticated via Facebook you can get the graph from the request as such

.. code-block:: python

    # persistent (graph stored in session)
    get_persistent_graph(request)
    require_persistent_graph(request)
    
    # not persistent
    get_facebook_graph(request)
    require_facebook_graph(request)

Typically you'll use the decorators in views where you access Facebook.


**Access token**

For mobile apps you'll sometimes get an access token directly

.. code-block:: python

    from open_facebook import OpenFacebook
    graph = OpenFacebook(access_token)









Tasks
=======

.. toctree::
   :maxdepth: 2

.. automodule:: django_facebook.tasks
    :members:
    
    .. autofunction:: extend_access_token(profile, access_token)
    .. autofunction:: store_likes(user, likes)
    .. autofunction:: store_friends(user, friends)
    .. autofunction:: get_and_store_likes(user, facebook)
    .. autofunction:: get_and_store_friends(user, facebook)
    .. autofunction:: remove_share(share)
    .. autofunction:: retry_open_graph_share(share)
    .. autofunction:: retry_open_graph_shares_for_user(share)


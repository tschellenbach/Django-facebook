Signals
-------

Django-facebook ships with a few signals that you can use to easily accommodate Facebook related activities with your project.

``facebook_user_registered`` signal is sent whenever a new user is registered by Django-facebook, for example:

.. code-block:: python

    from django_facebook.utils import get_user_model
    from django_facebook import signals

    def fb_user_registered_handler(sender, user, facebook_data, **kwargs):
        # Do something involving user here

    signals.facebook_user_registered.connect(user_registered, sender=get_user_model())


``facebook_pre_update`` signal is sent just before Django-facebook updates the profile model with Facebook data. If you want to manipulate Facebook or profile information before it gets saved, this is where you should do it. For example:

.. code-block:: python

    from django_facebook import signals
    from django_facebook.utils import get_user_model

    def pre_facebook_update(sender, user, profile, facebook_data, **kwargs):
        profile.facebook_information_updated = datetime.datetime.now()
        # Manipulate facebook_data here

    signals.facebook_pre_update.connect(pre_facebook_update, sender=get_user_model())


``facebook_post_update`` signal is sent after Django-facebook finishes updating the profile model with Facebook data. You can perform other Facebook connect or registration related processing here.

.. code-block:: python

    from django_facebook import signals
    from django_facebook.utils import get_user_model

    def post_facebook_update(sender, user, profile, facebook_data, **kwargs):
        # Do other stuff

    signals.facebook_post_update.connect(post_facebook_update, sender=get_user_model())

``facebook_post_store_friends`` signal is sent after Django-facebook finishes storing the user's friends.

.. code-block:: python

    from django_facebook import signals
    from django_facebook.utils import get_user_model

    def post_friends(sender, user, friends, current_friends, inserted_friends, **kwargs):
        # Do other stuff

    facebook_post_store_friends.connect(post_friends, sender=get_user_model())

``facebook_post_store_likes`` signal is sent after Django-facebook finishes storing the user's likes. This is usefull if you want to customize what topics etc to follow.

.. code-block:: python

    from django_facebook import signals
    from django_facebook.utils import get_user_model

    def post_likes(sender, user, likes, current_likes, inserted_likes, **kwargs):
        # Do other stuff

    facebook_post_store_likes.connect(post_likes, sender=get_user_model())
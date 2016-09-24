##############################################################################################
Django Facebook by Thierry Schellenbach (`mellowmorning.com <http://www.mellowmorning.com/>`_)
##############################################################################################

.. image:: https://secure.travis-ci.org/tschellenbach/Django-facebook.png?branch=master
        :target: https://travis-ci.org/tschellenbach/Django-facebook

.. image:: https://pypip.in/d/django-facebook/badge.png
        :target: https://pypi.python.org/pypi/django-facebook


Status
-------
Django and Facebook are both rapidly changing at the moment. Meanwhile, I'm caught up in a startup and don't have much spare time.
The library needs a good round of testing against the latest python, django and facebook graph API.
Contributions are strongly appreciated. Seriously, give github a try, fork and get started :)

News
----
* django-facebook will be dropping support for django < 1.8 since `django only supports <https://www.djangoproject.com/download/#supported-versions>`_ versions 1.8 and above.
  

Demo & About
------------

Django Facebook enables your users to easily register using the Facebook API.
It converts the Facebook user data and creates regular User and Profile objects.
This makes it easy to integrate with your existing Django application.

After registration Django Facebook gives you access to user's graph. Allowing for applications such as:

* Open graph/ Timeline functionality
* Seamless personalization
* Inviting friends
* Finding friends
* Posting to a users profile

Updates and tutorials can be found on my blog `mellowmorning <http://www.mellowmorning.com/>`_


Features
--------

* Access the Facebook API, from:
   * Your website (Using javascript OAuth)
   * Facebook canvas pages (For building facebook applications)
   * Mobile (Or any other flow giving you a valid access token)
* Django User Registration (Convert Facebook user data into a user model)
* Store likes, friends and user data locally.
* Facebook FQL access
* OAuth 2.0 compliant
* Automated reauthentication (For expired tokens)
* Includes Open Facebook (stable and tested Python client to the graph API)


Documentation
-------------

**Basics**

* `Installation <https://django-facebook.readthedocs.io/en/latest/installation.html>`_
* `Customizing <https://django-facebook.readthedocs.io/en/latest/customizing.html>`_
* `Settings <https://django-facebook.readthedocs.io/en/latest/settings.html>`_
* `Registration backends & Redirects <https://django-facebook.readthedocs.io/en/latest/registration_backend.html>`_

**Open Facebook API**

* `Getting an OpenFacebook object <https://django-facebook.readthedocs.io/en/latest/graph.html>`_
* `Making calls <https://django-facebook.readthedocs.io/en/latest/open_facebook/api.html>`_

**Advanced**

* `Mobile <https://django-facebook.readthedocs.io/en/latest/mobile.html>`_
* `Celery <https://django-facebook.readthedocs.io/en/latest/celery.html>`_
* `Signals <https://django-facebook.readthedocs.io/en/latest/signals.html>`_
* `Canvas <https://django-facebook.readthedocs.io/en/latest/canvas.html>`_


Contributing and Running tests
------------------------------
Tests are run from within the example project. You
can run them yourself as follows:

install from git

facebook_example/manage.py test django_facebook


**Vagrant**

A vagrant development setup is included in the GIT repo.
Assuming you have vagrant installed, simply type the following in your shell:

::

    # First get a fresh Django-Facebook checkout
    git clone git@github.com:tschellenbach/Django-facebook.git django-facebook

    # Go to the directory:
    cd django-facebook

    # Time to start Vagrant (grab a cup of coffee after this command, it'll take a while) :)
    vagrant up; vagrant provision

    # Finally done?
    vagrant ssh
    python manage.py runserver 0:8000

To have a working Django Facebook example up and running at 192.168.50.42:8000/facebook/example/.
For the facebook login to work simply map that ip to vagrant.mellowmorning.com
(Since Facebook checks the domain)

You can run the test suite by typing:

::

  python manage.py test django_facebook





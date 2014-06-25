Customizing
-----------

Now it's time to customize things a little. For a full example you can look at connect.html in the templates directory.

**Login flow**

1.) First load the css and javascript:

.. code-block:: django

    <link href="{{ STATIC_URL }}django_facebook/css/facebook.css" type="text/css" rel="stylesheet" media="all" />
    {% include 'django_facebook/_facebook_js.html' %}

If you encounter issues here you probably don't have django static files setup correctly.

2.) Next design the form

You can control redirects using next, register_next and error_next.

.. code-block:: django

    <form action="{% url 'facebook_connect' %}?facebook_login=1" method="post">
        <input type="hidden" value="{{ request.path }}" name="next" />
        <input type="hidden" value="{{ request.path }}" name="register_next" />
        <input type="hidden" value="{{ request.path }}" name="error_next" />
        {% csrf_token %}
        <input onclick="F.connect(this.parentNode); return false;" type="image" src="{{ STATIC_URL }}django_facebook/images/facebook_login.png" />
    </form>


**Connect flow**

Usually you'll also want to offer your users the ability to connect their existing account to Facebook.
You can control this by setting connect_facebook=1. The default behaviour is not to connect automatically.
(As this previously caused users to connect their accounts to Facebook by accident)

.. code-block:: django

    <form action="{% url 'facebook_connect' %}?facebook_login=1" method="post">
        <input type="hidden" value="1" name="connect" />
        {% csrf_token %}
        <a onclick="F.connect(this.parentNode); return false;" href="javascript:void(0);">Connect</a>
    </form>

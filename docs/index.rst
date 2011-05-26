######################################################################
Django Facebook by Thierry Schellenbach (http://www.mellowmorning.com)
######################################################################

Introduction
-----
Please contribute code :) 

This project is actively maintained and I appreciate improvements to the code.

Contact me here or `@tschellenbach <http://www.twitter.com/tschellenbach>`_

New in V2.0
------------------------
* canvas page support for facebook applications
* mobile facebook registration support (tested with titanium FB flow)
* less requirements (jinja, view decorator, django notify and cjson requirements removed)
* fql support
* django static support

About
---------------------
Django Facebook allows you to connect to the Facebook Open Graph API.
Integrated with Django it becomes easy to setup a login/register via Facebook flow for your users.

**Features**

* Access the Facebook API, from:
   * Your website (Using javascript OAuth)
   * Facebook canvas pages (For building facebook applications)
   * Mobile (Or any other flow giving you a valid access token)
* Django User Registration (Convert Facebook user data into a user model
* Use Facebook data to register a user with your Django app. Facebook connect using the open graph API.
* Facebook FQL access

Works best with (not required)
------------------------------
* Django registration
* Django 1.3
* Django static files
    
TODO (again help is appreciated!)
---------------------------------
* testing (especially a dummy FB api)
* separate user data conversion and FB api improvements
* fully replace the facebook GraphAPI which they no longer support
   

Installation
------------

Download the source code or use pip install django_facebook.


**Create a Facebook App**

In case you don't yet have a facebook app. You need an app to use the open graph api and make the login process work.
You can create a facebook app at this url: http://www.facebook.com/developers/createapp.php 

**Settings**

Define the following settings in your settings.py file:

::

    FACEBOOK_API_KEY
    FACEBOOK_APP_ID
    FACEBOOK_APP_SECRET
        
**Url config, context processor, auth backend**

::

	add django facebook to your installed apps
	'django_facebook',
    add this line to your url config
    (r'^facebook/', include('django_facebook.urls')),
    add this line to your context processors
    'django_facebook.context_processors.facebook',
    add this to your AUTHENTICATION_BACKENDS
    'django_facebook.auth_backends.FacebookBackend',

**Update your models**

Add the following fields to your profile model:

::

    about_me = models.TextField(blank=True, null=True)
    facebook_id = models.IntegerField(blank=True, null=True)
    facebook_name = models.CharField(max_length=255, blank=True, null=True)
    facebook_profile_url = models.TextField(blank=True, null=True)
    website_url = models.TextField(blank=True, null=True)
    blog_url = models.TextField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True, upload_to='profile_images')
    date_of_birth = models.DateField(blank=True, null=True)
    raw_data = models.TextField(blank=True, null=True)

An abstract model is specified for convenience django_facebook/models.py FacebookProfileModel
    
**Check the example**

Right now you should have a working registration/connect/login in flow available at /facebook/connect/
Test if everything is working and ensure you didn't miss a step somewhere.

**Common bugs**

Django Facebook expects that you are using static files in order to load the required javascript.
If you are not using staticfiles you should load facebook.js provided in the static directory manually.

Another common issue are the url matching settings from Facebook. Facebook requires you to fill in a domain for your application.
In order for things to work with local development you need to use the same domain. So if you production site is www.mellowmorning.com you 
should run your development server on something like local.mellowmorning.com in order for facebook to allow authentication.
 
If you encounter any difficulties please open an issue.

**Customize and integrate into your site**

This is the hardest step of the install. 
For an example you can look at connect.html in the templates directory.

First load the javascript (it loads the facebook library asynchronously).
I recommend that you insert this code at the bottom of your page.

::

    <script src="{{ MEDIA_URL }}js/original/facebook.js" type="text/javascript"></script>
    <script>
    facebookAppId = '{{ FACEBOOK_APP_ID }}';
    function facebookJSLoaded(){
    FB.init({appId: facebookAppId, status: false, cookie: true, xfbml: true});
    }
    window.fbAsyncInit = facebookJSLoaded;
    F = new facebookClass(facebookAppId);
    F.load();
    </script>

Subsequently implement a form which calls Facebook via javascript.
Note that you can control which page to go to after connect using the next input field.

::

<form action="{% url facebook_connect %}?facebook_login=1" method="post">
<a href="javascript:void(0);" style="font-size: 20px;" onclick="F.connect(this.parentNode);">Register, login or connect with facebook</a>
<input type="hidden" value="{{ request.path }}" name="next" />
</form>
    
    
Django Jobs
-----------
Do you also see the beauty in clean code? Are you experienced with high scalability web apps?
Currently we're looking for additional talent over at our Amsterdam office.
Feel free to drop me a line at my personal email for more information: thierryschellenbach[at]gmail.com



	

Contents:

.. toctree::
   :maxdepth: 2

   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


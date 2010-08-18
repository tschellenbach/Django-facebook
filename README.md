h1. Django Facebook by Thierry Schellenbach (http://www.mellowmorning.com)

Login and registration functionality using the new facebook open graph api.
- Actually creates user models and profiles
- Robust facebook user data -> django account conversion

h2. Required django apps

    django.contrib.auth (Django core app, included)
    django-registration
    
h2. Additional dependencies 

    python-cjson
    
h2. Implementation

h3. Step 1 - Settings

Define the settings in django_facebook/settings.py in your settings.py file
        
h3. Step 2 - Url config

add 
    (r'^facebook/', include('django_facebook.urls')),
to your global url file 
        
h3. Step 3 - Ensure the FB JS api is available on all pages you want to login
[Facebook JS API](http://developers.facebook.com/docs/reference/javascript/)
    
h3. Step 4 - Update your models
        
Add to your user profile model
    about_me = models.TextField(blank=True, null=True)
    facebook_id = models.IntegerField(blank=True, null=True)
    facebook_name = models.CharField(max_length=255, blank=True, null=True)
    facebook_profile_url = framework_fields.URLTextField(blank=True, null=True)
    website_url = framework_fields.URLTextField(blank=True, null=True)
    blog_url = framework_fields.URLTextField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
h3. Step 5 - Template
    See examples/connect.html
    
    
For more details, see the [Facebook docs](http://developers.facebook.com/docs/).
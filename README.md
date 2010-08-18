# Django Facebook by Thierry Schellenbach (http://www.mellowmorning.com)

Login and registration functionality using the new facebook open graph api.

* Actually creates user models and profiles
* Robust facebook user data -> django account conversion

## Required django apps

* django.contrib.auth (Django core app, included)
* django-registration
    
## Additional dependencies 

* python-cjson
    
## Implementation

### Step 1 - Settings

Define the settings in `django_facebook/settings.py` in your `settings.py` file.
        
### Step 2 - Url config

add 

    url(r'^facebook/', include('django_facebook.urls')),

to your global `url.py` file.
        
### Step 3 - Ensure the FB JS api is available on all pages you want to login

[Facebook JS API](http://developers.facebook.com/docs/reference/javascript/)
    
### Step 4 - Update your models
        
Add to your user profile model

    about_me = models.TextField(blank=True, null=True)
    facebook_id = models.IntegerField(blank=True, null=True)
    facebook_name = models.CharField(max_length=255, blank=True, null=True)
    facebook_profile_url = framework_fields.URLTextField(blank=True, null=True)
    website_url = framework_fields.URLTextField(blank=True, null=True)
    blog_url = framework_fields.URLTextField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
### Step 5 - Template

See `examples/connect.html`.
        
For more details, see the [Facebook docs](http://developers.facebook.com/docs/).
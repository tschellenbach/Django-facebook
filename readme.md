Django Facebook by Thierry Schellenbach (http://www.mellowmorning.com)
====

Login and registration functionality using the new facebook open graph api.
- Actually creates user models and profiles
- Robust facebook user data -> django account conversion

Requires:

    Facebook python sdk
    Facebook JS sdk
    django registration
    django auth
    cjson
    
Implementation:

    Step 1 - Settings:
        Define the settings in django_facebook/settings.py in your settings.py file
        
    Step 2 - Url config:
        add 
        (r'^facebook/', include('django_facebook.urls')),
        to your global url file 
        
    Step 3 - Ensure the FB JS api is available on all pages you want to login
    [Facebook JS API](http://developers.facebook.com/docs/reference/javascript/)
    
    Step 4 - Template
    <form class="facebook_connect" action="{% url facebook_connect %}?facebook_login=1" method="post">
        <a href="javascript:void(0);" onclick="F.connect(this.parentNode);">Register with facebook</a>
        <input type="hidden" name="next" value="/">
    </form>
    
    //see django_facebook/media/js/facebook.js for the F.connect implementation
    
    
[Facebook docs](http://developers.facebook.com/docs/)
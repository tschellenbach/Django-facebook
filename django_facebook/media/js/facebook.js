

facebookClass = function() { this.initialize.apply(this, arguments); };
facebookClass.prototype = {
    initialize: function (appId) {
		this.appId = appId;
		
		var scope = this;
		function javascriptLoaded() {
			scope.javascriptLoaded.call(scope);
		}
    },
    
    connect: function (formElement, requiredPerms) {
    	//,'publish_stream','offline_access'
    	requiredPerms = requiredPerms || ['email','user_about_me','user_birthday','user_website'];
    	FB.login(function(response) {
    		formElement.submit();
    	},
    	{perms: requiredPerms.join(',')}
    	);
    },
	
	load: function () {
		var facebookScript = document.getElementById('facebook_js');
		if (!facebookScript) {
			var e = document.createElement('script');
			e.type = 'text/javascript';
			e.src = document.location.protocol + '//connect.facebook.net/en_US/all.js';
			e.async = true;
			e.id = 'facebook_js';
			document.getElementById('fb-root').appendChild(e);
		}
	}
};







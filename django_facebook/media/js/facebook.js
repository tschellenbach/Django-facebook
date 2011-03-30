facebookClass = function() { this.initialize.apply(this, arguments); };
facebookClass.prototype = {
    initialize: function () {
    },
    
    connect: function (formElement) {
    	//,'publish_stream','offline_access'
    	var requiredPerms = ['email','user_about_me','user_birthday','user_website'];
    	FB.login(function(response) {
    		formElement.submit();
    	},
    	{perms: requiredPerms.join(',')}
    	);
    },
    
    api: function() {
    	var destination = arguments[0];
    	var method, options;
    	if (typeof(arguments[1]) == 'string') {
    		method = arguments[1];
    	} else {
    		method = 'get';
    	}
    	if (typeof(arguments[1]) == 'object') {
    		options = arguments[1];
    	} else if (typeof(arguments[2]) == 'object') {
    		options = arguments[2];
    	} else {
    		options = {};
    	}
    	options['metadata'] = '1';
    	var handler = jQuery.proxy(this.debugResponseHandler, this);
    	return FB.api(destination, method, options, handler);
    	
    },
    
    debugResponseHandler: function(response) {
    	console.log(response);
    	
    	if (response.metadata && response.metadata.connections) {
    		console.log(response.metadata.connections);
    	}
    }
};

F = new facebookClass();
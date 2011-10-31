facebookClass = function() {
    this.initialize.apply(this, arguments);
};
facebookClass.prototype = {
    initialize : function(appId) {
        this.appId = appId;

        var scope = this;
        function javascriptLoaded() {
            scope.javascriptLoaded.call(scope);
        }
        
        var iphone = navigator.userAgent.match(/iPhone/i)
        var ipod = navigator.userAgent.match(/iPod/i);
        var ipad = navigator.userAgent.match(/iPad/i);
        var ithing = iphone || ipod || ipad;
        this.ithing = ithing;
    },

    requirePermissions : function(requiredPerms, callback) {
        /*
         * Checks for the required permissions and asks for them if they are
         * missing Callback is called with the resposne of the login function or
         * the permission api call
         * 
         * requiredPerms is a list of permissions
         */
        var requiredPermString = requiredPerms.join(',');

        FB.api('/me/permissions', function(response) {
            // above request will fail if the user isn't yet authenticated
                var permissions = response.data ? response.data[0] : response;

                // check if all permissions are met
                var permissionsGranted = true;
                for ( var i = 0; i < requiredPerms.length; i++) {
                    var requiredPerm = requiredPerms[i];
                    if (!(requiredPerm in permissions)) {
                        permissionsGranted = false;
                        break;
                    }
                }
                // login or go straight to callback
                if (permissionsGranted) {
                    callback(response)
                } else {
                    FB.login(function() {
                        console.log(arguments)
                    }, {
                        'scope' : 'offline_access'
                    });
                }
            });
    },

    connect : function(formElement, requiredPerms) {
        if (this.ithing) {
            formElement.submit();
            return false;
        }
        requiredPerms = requiredPerms
                || [ 'email', 'user_about_me', 'user_birthday', 'user_website' ];
        FB.login(function(response) {
            var accessToken = response.authResponse.accessToken;
            formElement.submit();
        }, {
            scope : requiredPerms.join(',')
        });
    },

    load : function() {
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

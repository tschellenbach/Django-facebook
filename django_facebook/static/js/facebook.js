


/*
Maps locale from django to Facebook
scraped like this from FB:
curl https://www.facebook.com/translations/FacebookLocales.xml -s | grep "<representation>" FacebookLocales.xml | sed 's@<\([^<>][^<>]*\)>\([^<>]*\)</\1>@\2@g'
* */
fbLocales = ["af_ZA", "ar_AR", "az_AZ", "be_BY", "bg_BG", "bn_IN", "bs_BA", 
    "ca_ES", "cs_CZ", "cy_GB", "da_DK", "de_DE", "el_GR", "en_GB", "en_PI", 
    "en_UD", "en_US", "eo_EO", "es_ES", "es_LA", "et_EE", "eu_ES", "fa_IR", 
    "fb_LT", "fi_FI", "fo_FO", "fr_CA", "fr_FR", "fy_NL", "ga_IE", "gl_ES", 
    "he_IL", "hi_IN", "hr_HR", "hu_HU", "hy_AM", "id_ID", "is_IS", "it_IT", 
    "ja_JP", "ka_GE", "ko_KR", "ku_TR", "la_VA", "lt_LT", "lv_LV", "mk_MK", 
    "ml_IN", "ms_MY", "nb_NO", "ne_NP", "nl_NL", "nn_NO", "pa_IN", "pl_PL", 
    "ps_AF", "pt_BR", "pt_PT", "ro_RO", "ru_RU", "sk_SK", "sl_SI", "sq_AL", 
    "sr_RS", "sv_SE", "sw_KE", "ta_IN", "te_IN", "th_TH", "tl_PH", "tr_TR", 
    "uk_UA", "vi_VN", "zh_CN", "zh_HK", "zh_TW"];

fbLocaleMapping = {};
for (var i=0; i<fbLocales.length;i++){
    var k = fbLocales[i].split("_")[0];
    fbLocaleMapping[k] = fbLocales[i];
    fbLocaleMapping[fbLocales[i]] = fbLocales[i];
}

facebookClass = function() { this.initialize.apply(this, arguments); };
facebookClass.prototype = {
    initialize: function (appId) {
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
    
    getDefaultScope : function() {
        var defaultScope;
       if (typeof(facebookDefaultScope) != 'undefined') {
            defaultScope = facebookDefaultScope;  
       } else {
           defaultScope = ['email', 'user_about_me', 'user_birthday', 'user_website'];
       }
       return defaultScope;
    },
    
    connect: function (formElement, requiredPerms) {
        if (this.ithing) {
            return formElement.submit();
        }
        requiredPerms = requiredPerms || this.getDefaultScope();
        this.connectLoading('A Facebook pop-up has opened, please follow the instructions to sign in.');
        var scope = this;
        FB.login(function(response) {
            if (response.status == 'unknown') {
                scope.connectLoading('Sorry, we couldn\'t log you in. Please try again.', true, true);
            } else {
                //showloading
                scope.connectLoading('Now loading your profile...');
                //submit the form
                formElement.submit();
            }
        },
        {scope: requiredPerms.join(',')}
        );
    },
    
    connectLoading: function (message, closeable, hideLoading) {
        /*
         * Show a loading lightbox to clarify what's happening to the user
         */
        var facebookMessage = document.getElementById('facebook_message');
        var facebookContainer = document.getElementById('facebook_container');
        if (!facebookMessage) {
            var container = document.createElement('div');
            container.id = 'facebook_container';
            var html = '<div id="facebook_shade"></div>\
                <div id="facebook_wrapper">\
                    <div id="facebook_lightbox">\
                        <div id="facebook_message" />{{ message }}</div>\
                        <img id="facebook_loading" src="' + staticUrl + 'images/facebook_loading.gif" alt="..."/>\
                        <div id="facebook_close" style="display: none" onclick="document.getElementById(\'facebook_container\').style.display=\'none\';"></div>\
                    </div>\
                </div>';
            html = html.replace('{{ message }}', message);
            container.innerHTML = html;
            document.body.appendChild(container);
            facebookMessage = document.getElementById('facebook_message');
            facebookContainer = document.getElementById('facebook_container');
        }
        facebookMessage.innerHTML = message;
        facebookContainer.style.display = message ? 'block' : 'none';
        document.getElementById('facebook_close').style.display = closeable ? 'block' : 'none';
        document.getElementById('facebook_loading').style.display = hideLoading ? 'none' : 'inline';
        
        //set the correct top
        var requiredTop = this.getViewportScrollY();
        document.getElementById('facebook_lightbox').style.top = requiredTop + 'px';
    },
    
    
    load: function () {
        var facebookScript = document.getElementById('facebook_js');
        if (!facebookScript) {
            var e = document.createElement('script');
            e.type = 'text/javascript';
            // gets the locale, tries to get the facebook synonym and 
            // the checks if it is a valid FB locale
            var fbLocale = "en_US";
            if(typeof(locale) != 'undefined') {
                if (locale in fbLocaleMapping) {
                    fbLocale = fbLocaleMapping[locale];
                }
            }
            var fbLocation = '//connect.facebook.net/' + fbLocale + '/all.js';
            e.src = document.location.protocol + fbLocation;
            e.async = true;
            e.id = 'facebook_js';
            document.getElementById('fb-root').appendChild(e);
        }
    },
    
    getViewportScrollY: function() {
        var scrollY = 0;
        if( document.documentElement && document.documentElement.scrollTop ) {
          scrollY = document.documentElement.scrollTop;
        }
        else if( document.body && document.body.scrollTop ) {
          scrollY = document.body.scrollTop;
        }
        else if( window.pageYOffset ) {
          scrollY = window.pageYOffset;
        }
        else if( window.scrollY ) {
          scrollY = window.scrollY;
        }
        return scrollY;
    }
};




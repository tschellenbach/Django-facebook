from django.contrib import admin
from django.conf import settings
from django.core.urlresolvers import reverse
from django_facebook import admin_actions
from django_facebook import models


class FacebookUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'facebook_id',)
    search_fields = ('name',)


class FacebookLikeAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'category', 'facebook_id',)
    search_fields = ('name',)
    filter_fields = ('category',)


class FacebookProfileAdmin(admin.ModelAdmin):
    list_display = ('image_', 'user_', 'facebook_name', 'facebook_id',)

    raw_id_fields = ('user',)

    search_fields = ('facebook_name', 'facebook_id',)

    def image_(self, instance):
        return """<span style="
        background-image: url({0});
        background-size: cover;
        width: 21px;
        height: 21px;
        display: inline-block;
        outline: 1px solid #DDD;
        position: absolute;
        margin-top: -3px;
    "></span>""".format(
            instance.image.url
        )
    image_.allow_tags = True

    def user_(self, instance):
        admin_url = reverse('admin:auth_user_change', args=[instance.user.pk])
        return '<a href="{0}">{1}</a>'.format(
            admin_url,
            instance.user
        )
    user_.allow_tags = True
    
    
def facebook_profile(open_graph_share):
    '''
    Nicely displayed version of the facebook user
    with user id and image and link to facebook :)
    '''
    user = open_graph_share.user
    profile = user.get_profile()
    facebook_id = profile.facebook_id
    facebook_url = 'http://www.facebook.com/%s/' % facebook_id
    link = '<p><a href="%s"><img src="http://graph.facebook.com/%s/picture/?type=large" width="100px" style="float:left"/>%s</a><br/></p>' % (facebook_url, facebook_id, facebook_id)
    return link

facebook_profile.allow_tags = True
facebook_profile.short_description = 'Profile'


class OpenGraphShareAdmin(admin.ModelAdmin):
    raw_id_fields = ['user']
    list_filter = ['created_at', 'completed_at', 'action_domain']
    list_display = ['user', 'action_domain', facebook_profile, 'completed_at', 'error_message']
    actions = [admin_actions.retry_open_graph_share]
    date_hierarchy = 'created_at'


if settings.AUTH_PROFILE_MODULE == 'django_facebook.FacebookProfile':
    admin.site.register(models.FacebookProfile, FacebookProfileAdmin)

admin.site.register(models.FacebookUser, FacebookUserAdmin)
admin.site.register(models.FacebookLike, FacebookLikeAdmin)

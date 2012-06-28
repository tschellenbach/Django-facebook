from django.conf import settings



from django.contrib import admin
from django_facebook import models

class FacebookUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'facebook_id',)
    search_fields = ('name',)


class FacebookLikeAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'category', 'facebook_id',)
    search_fields = ('name',)
    filter_fields = ('category', )

if settings.AUTH_PROFILE_MODULE ==  'django_facebook.FacebookProfile':
    admin.site.register(models.FacebookProfile)

admin.site.register(models.FacebookUser, FacebookUserAdmin)
admin.site.register(models.FacebookLike, FacebookLikeAdmin)

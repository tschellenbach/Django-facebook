from django.contrib import admin
from django_facebook import models


class FacebookUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'facebook_id',)
    search_fields = ('name',)
    raw_id_fields = ('user',)
    
    
class FacebookLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'category', 'facebook_id',)
    raw_id_fields = ('user',)
    search_fields = ('name',)
    filter_fields = ('category', )


admin.site.register(models.FacebookUser, FacebookUserAdmin)
admin.site.register(models.FacebookLike, FacebookLikeAdmin)
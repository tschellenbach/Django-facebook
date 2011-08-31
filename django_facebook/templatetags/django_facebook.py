from django import template
from django.conf import settings

register = template.Library()
    
@register.inclusion_tag('django_facebook/init.html')
def facebook_init():
    return {'facebook_app_id': settings.FACEBOOK_APP_ID}


@register.inclusion_tag('django_facebook/connect_button.html',takes_context=True)
def connect_button(context):
    next = context['request'].GET.get('next', '')
    return {'next': next}


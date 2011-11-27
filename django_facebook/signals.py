from django.dispatch import Signal


# Sent right after user is created
facebook_user_registered = Signal(providing_args=['user', 'facebook_data'])

# Sent after user is created, before profile is updated with data from Facebook
facebook_pre_update = Signal(providing_args=['profile', 'facebook_data'])
facebook_post_update = Signal(providing_args=['profile', 'facebook_data'])
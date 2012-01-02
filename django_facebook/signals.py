from django.dispatch import Signal


# Sent right after user is created
facebook_user_registered = Signal(providing_args=['user', 'facebook_data'])

# Sent after user is created, before profile is updated with data from Facebook
facebook_pre_update = Signal(providing_args=['profile', 'facebook_data'])
facebook_post_update = Signal(providing_args=['profile', 'facebook_data'])

# Sent after storing the friends from graph to db
facebook_post_store_friends = Signal(providing_args=['user', 'friends', 'current_friends', 'inserted_friends'])

# Sent after storing the likes from graph to db
facebook_post_store_likes = Signal(providing_args=['user', 'likes', 'current_likes', 'inserted_likes'])
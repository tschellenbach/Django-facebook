




user_data = {}


user_data['no_email'] = {'first_name': 'Thierry', 'last_name': 'Schellenbach', 'verified': True, 'name': 'Thierry Schellenbach', 'gender': 'man', 'image': 'http://graph.facebook.com/me/picture?type=large', 'updated_time': '2010-04-01T14:26:55+0000', 'birthday': '04/07', 'link': 'http://www.facebook.com/profile.php?id=1225707780', 'location': {'id': None, 'name': None}, 'timezone':-5, 'id': '1225707780', 'image_thumb': 'http://graph.facebook.com/me/picture'}
user_data['tschellenbach'] = {'email': 'fake@mellowmorning.com', 'first_name': 'Thierry', 'last_name': 'Schellenbach', 'verified': True, 'name': 'Thierry Schellenbach', 'gender': 'man', 'image': 'http://graph.facebook.com/me/picture?type=large', 'updated_time': '2010-04-01T14:26:55+0000', 'birthday': '04/07', 'link': 'http://www.facebook.com/profile.php?id=1225707780', 'location': {'id': None, 'name': None}, 'timezone':-5, 'id': '1225707780', 'image_thumb': 'http://graph.facebook.com/me/picture'}
user_data['new_user'] = {'email': 'fake_new@mellowmorning.com', 'first_name': 'Thierry', 'last_name': 'Schellenbach', 'verified': True, 'name': 'Thierry Schellenbach', 'gender': 'male', 'image': 'http://graph.facebook.com/me/picture?type=large', 'updated_time': '2010-04-01T14:26:55+0000', 'birthday': '04/07', 'link': 'http://www.facebook.com/profile.php?id=1225707780', 'location': {'id': None, 'name': None}, 'timezone':-5, 'id': '1225707781', 'image_thumb': 'http://graph.facebook.com/me/picture'}
user_data['no_birthday'] = {'website': 'www.pytell.com', 'first_name': 'Jonathan', 'last_name': 'Pytell', 'verified': True, 'name': 'Jonathan Pytell', 'image': 'http://graph.facebook.com/me/picture?type=large', 'updated_time': '2010-01-01T18:13:17+0000', 'link': 'http://www.facebook.com/jpytell', 'location': {'id': None, 'name': None}, 'timezone':-4, 'id': '776872663', 'image_thumb': 'http://graph.facebook.com/me/picture'}
user_data['partial_birthday'] = {'first_name': 'Thierry', 'last_name': 'Schellenbach', 'verified': True, 'name': 'Thierry Schellenbach', 'gender': 'man', 'image': 'http://graph.facebook.com/me/picture?type=large', 'updated_time': '2010-04-01T14:26:55+0000', 'birthday': '04/07', 'link': 'http://www.facebook.com/profile.php?id=1225707780', 'location': {'id': None, 'name': None}, 'timezone':-5, 'id': '1225707780', 'image_thumb': 'http://graph.facebook.com/me/picture'}
user_data['short_username'] = {'email': 'f@mellowmorning.com', 'first_name': 'Thierry', 'last_name': 'Schellenbach', 'verified': True, 'name': 'Thierry Schellenbach', 'gender': 'man', 'image': 'http://graph.facebook.com/me/picture?type=large', 'updated_time': '2010-04-01T14:26:55+0000', 'birthday': '04/07', 'link': 'http://www.facebook.com/profile.php?id=1225707780', 'location': {'id': None, 'name': None}, 'timezone':-5, 'id': '1225707782', 'image_thumb': 'http://graph.facebook.com/me/picture'}

user_data['same_username'] = user_data['short_username'].copy()
user_data['same_username'].update(dict(id='1111111', email='t@fake.com'))

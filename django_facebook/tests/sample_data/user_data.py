




user_data = {}


user_data['no_email'] = {'first_name': 'Thierry', 'last_name': 'Schellenbach', 'verified': True, 'name': 'Thierry Schellenbach', 'gender': 'man', 'image': 'http://graph.facebook.com/me/picture?type=large', 'updated_time': '2010-04-01T14:26:55+0000', 'birthday': '04/07', 'link': 'http://www.facebook.com/profile.php?id=1225707780', 'location': {'id': None, 'name': None}, 'timezone':-5, 'id': '1225707780', 'image_thumb': 'http://graph.facebook.com/me/picture'}
user_data['tschellenbach'] = {'email': 'fake@mellowmorning.com', 'first_name': 'Thierry', 'last_name': 'Schellenbach', 'verified': True, 'name': 'Thierry Schellenbach', 'gender': 'man', 'image': 'http://graph.facebook.com/me/picture?type=large', 'updated_time': '2010-04-01T14:26:55+0000', 'birthday': '04/07', 'link': 'http://www.facebook.com/profile.php?id=1225707780', 'location': {'id': None, 'name': None}, 'timezone':-5, 'id': '1225707780', 'image_thumb': 'http://graph.facebook.com/me/picture'}
user_data['new_user'] = {'email': 'fake_new@mellowmorning.com', 'first_name': 'Thierry', 'last_name': 'Schellenbach', 'verified': True, 'name': 'Thierry Schellenbach', 'gender': 'male', 'image': 'http://graph.facebook.com/me/picture?type=large', 'updated_time': '2010-04-01T14:26:55+0000', 'birthday': '04/07', 'link': 'http://www.facebook.com/profile.php?id=1225707780', 'location': {'id': None, 'name': None}, 'timezone':-5, 'id': '1225707781', 'image_thumb': 'http://graph.facebook.com/me/picture'}
user_data['no_birthday'] = {'website': 'www.pytell.com', 'first_name': 'Jonathan', 'last_name': 'Pytell', 'verified': True, 'name': 'Jonathan Pytell', 'image': 'http://graph.facebook.com/me/picture?type=large', 'updated_time': '2010-01-01T18:13:17+0000', 'link': 'http://www.facebook.com/jpytell', 'location': {'id': None, 'name': None}, 'timezone':-4, 'id': '776872663', 'image_thumb': 'http://graph.facebook.com/me/picture'}
user_data['partial_birthday'] = {'first_name': 'Thierry', 'last_name': 'Schellenbach', 'verified': True, 'name': 'Thierry Schellenbach', 'gender': 'man', 'image': 'http://graph.facebook.com/me/picture?type=large', 'updated_time': '2010-04-01T14:26:55+0000', 'birthday': '04/07', 'link': 'http://www.facebook.com/profile.php?id=1225707780', 'location': {'id': None, 'name': None}, 'timezone':-5, 'id': '1225707780', 'image_thumb': 'http://graph.facebook.com/me/picture'}
user_data['short_username'] = {'email': 'f@mellowmorning.com', 'first_name': 'Thierry', 'last_name': 'Schellenbach', 'verified': True, 'name': 'Thierry Schellenbach', 'gender': 'man', 'image': 'http://graph.facebook.com/me/picture?type=large', 'updated_time': '2010-04-01T14:26:55+0000', 'birthday': '04/07', 'link': 'http://www.facebook.com/profile.php?id=1225707780', 'location': {'id': None, 'name': None}, 'timezone':-5, 'id': '1225707782', 'image_thumb': 'http://graph.facebook.com/me/picture'}

user_data['same_username'] = user_data['short_username'].copy()
user_data['same_username'].update(dict(id='1111111', email='t@fake.com'))


user_data['unicode_string'] = {'bio': ';= Te conformas con UN PERD\xd3N y UN SIMPLE ABRAZO (8) . -\r\n\r\n(A)\r\n\r=r\n; SOLOS mir\xe1ndonos a LOS OJOS (8) -\r\n\r\n\r\n, TUS BESOS me hacen= SONRE\xcdR ~',
 'birthday': '01/30/1992',
 'email': 'roc=io.delcarre@hotmail.com',
 'first_name': 'Roc\xedo Bel\xe9n',
 'gender': 'female',
 'id': '1359572466',
 'image': 'https://graph.facebook.com/me/pi=cture?type=3Dlarge&access_token=3D100314226679773|2.NrOOTmWNwjl5j3jQZCokVA_=_.86400.1303502400.4-1359572466|tHS0hZxMu1znILTlVJpWYWpLTi4',
 'image_thumb': 'https://graph.facebook.com/me=/picture?access_token=3D100314226679773|2.NrOOTmWNwjl5j3jQZCokVA__.86400.13=03502400.4-1359572466|tHS0hZxMu1znILTlVJpWYWpLTi4',
 'last_name': 'del =Carre',
 'link': 'http://www.facebook.com/Rocio.delCarre',
 'local=e': 'es_LA',
 'name': 'Roc\xedo Bel\xe9n del Carre',
 'timezone':-3,
 'update=d_time': '2011-04-21T19:41:20+0000',
 'username': 'Rocio.delCarre',
 'verified': True,
 'website': '~ Vay\xe1monos de ac\xe1 , que TO=DO el resto NO importa (8)'
}

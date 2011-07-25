import unittest

class TestOpenFacebook(unittest.TestCase):
    def test_setting_likes(self):
        pass




def test_facebook():
    cookie = 'F7cndfQuSIkcVHWIgg_SHQ4LIDJXeeHhiXUNjesOw5g.eyJhbGdvcml0aG0iOiJITUFDLVNIQTI1NiIsImNvZGUiOiJVMTZuMFNoWVUxSTJ5VEFJMVZ0RmlvZTdhRVRaaEZ4cGV5d1hwYnZvOUprLmV5SnBkaUk2SW1OcmFGVXlWR053ZDA1VlMwSTRlUzFzZDA1WmFtY2lmUS5rZl9RTUhCMnVFTVh5YW83UU5UcnFGMlJzOGxxQUxrM1AxYm8zazBLMm5YUXpOZW5LSVlfczBVV3ZNbE1jTXAzcE04TXNLNVVDQUpjWlQ1N1ZaZXFkS3ZPeXRFbmdoODFxTmczTXVDeTBHNjB6WjFBOWZGZlpHenVDejdKSEVSSCIsImlzc3VlZF9hdCI6MTMxMTYwMDEyNywidXNlcl9pZCI6Nzg0Nzg1NDMwfQ'
    print FacebookAuthorization.parse_signed_data(cookie)
    
    token = FacebookAuthorization.get_app_access_token()
    
    code = 'hPcK30IZB4G01VFitzWfR4P0JkF6UAmZ6PpRtUlANNQ.eyJpdiI6ImpkWTVFSEdQbVFpb1dBbHU3blUtdFEifQ.hKs8HRWGuZ7aRnspguBW1SjLrKCmdp0KNS6tJNvcikQnLjyZgEnMSqTdPM4WGZqI5UQl8uTr2cppwSm67eOQ-cIRUknXRq5wIwADO6PdJ7ZhTlKMqiTXJHfMqTmml6FO'
    user_token = FacebookAuthorization.convert_code(code)
    print user_token
    #print FacebookAuthorization.create_test_user(token)
    token = '215464901804004|2.AQBHGHuWRllFbN4E.3600.1311465600.0-100002619711402|EtaLBkqHGsTa0cpMlFA4bmL4aAc'
    token = '215464901804004|2.AQAwYr7AYNkKS9Rn.3600.1311469200.0-100002646981608|NtiF-ioL-98NF5juQtN2UXc0wKU'
    token = '215464901804004|b8d73771906a072829857c2f.0-100002661892257|DALPDLEZl4B0BNm0RYXnAsuri-I'
    facebook = OpenFacebook(token)
    
    result = facebook.fql('SELECT name FROM user WHERE uid = me()')
    print 'result', result
    albums = facebook.get('me/albums')
    album_names = [album['name'] for album in albums['data']]
    print album_names
    
    print facebook.me()
    
    print facebook.get('fashiolista')
    
    print facebook.set('fashiolista/likes')
    
    #print facebook.post_on_wall('me', 'the writing is one the wall')
    
    
#    for photo in photo_urls:
#        print facebook.set('me/photos', url=photo, message='the writing is one the wall', name='FashiolistaTest')
        
#    albums = facebook.get('me/albums')
#    album_response = facebook.set('me/albums', params=dict(name='FashiolistaSuperAlbum', message='Your latest fashion finds'))
#    album_id = album_response['id']
#    for photo in photo_urls:
#        print facebook.set('%s/photos' % album_id, url=photo, message='the writing is one the wall', name='FashiolistaTest')

    photo_urls = [
        'http://e.fashiocdn.com/images/entities/0/7/B/I/9/0.365x365.jpg',
        'http://e.fashiocdn.com/images/entities/0/5/e/e/r/0.365x365.jpg',
    ]
    for photo in photo_urls:
        print facebook.set('me/feed', message='the writing is one the wall', picture=photo)
    
    #print facebook.get('me/permissions')
    print facebook.get('me/feed')
    #this should give a lazy iterable instead of the default result..
    
    #print facebook.get_many('cocacola', 'me')
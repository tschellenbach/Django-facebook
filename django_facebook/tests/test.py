from __future__ import with_statement
from django.contrib.auth.models import AnonymousUser
from django_facebook import exceptions as facebook_exceptions
from django_facebook.api import get_facebook_graph
from django_facebook.connect import connect_user, CONNECT_ACTIONS
from django_facebook.official_sdk import GraphAPIError
from django_facebook.tests.base import FacebookTest
import logging
import unittest
from django.utils import simplejson
from django_facebook.auth_backends import FacebookBackend




logger = logging.getLogger(__name__)

'''
TODO
The views are currently untested,
only the underlying functionality is.
(need to fake facebook cookie stuff to correctly test the views)
'''
    
class UserConnectTest(FacebookTest):
    '''
    Tests the connect user functionality
    '''
    fixtures = ['users.json']
    
    def test_full_connect(self):
        #going for a register, connect and login
        facebook = get_facebook_graph(access_token='short_username', persistent_token=False)
        action, user = connect_user(self.request, facebook_graph=facebook)
        assert action == CONNECT_ACTIONS.REGISTER
        action, user = connect_user(self.request, facebook_graph=facebook)
        assert action == CONNECT_ACTIONS.CONNECT
        self.request.user = AnonymousUser()
        action, user = connect_user(self.request, facebook_graph=facebook)
        assert action == CONNECT_ACTIONS.LOGIN
        
    def test_utf8(self):
        facebook = get_facebook_graph(access_token='unicode_string', persistent_token=False)
        profile_data = facebook.facebook_profile_data()
        action, user = connect_user(self.request, facebook_graph=facebook)
    
    def test_invalid_token(self):
        self.assertRaises(AssertionError, connect_user, self.request, access_token='invalid')

    def test_no_email_registration(self):
        self.assertRaises(facebook_exceptions.IncompleteProfileError, connect_user, self.request, access_token='no_email')
    
    def test_current_user(self):
        facebook = get_facebook_graph(access_token='tschellenbach', persistent_token=False)
        action, user = connect_user(self.request, facebook_graph=facebook)
        assert action == CONNECT_ACTIONS.LOGIN
    
    def test_new_user(self):
        facebook = get_facebook_graph(access_token='new_user', persistent_token=False)
        action, user = connect_user(self.request, facebook_graph=facebook)
    
    def test_short_username(self):
        facebook = get_facebook_graph(access_token='short_username', persistent_token=False)
        action, user = connect_user(self.request, facebook_graph=facebook)
        assert len(user.username) > 4
        assert action == CONNECT_ACTIONS.REGISTER
        
    def test_gender(self):
        facebook = get_facebook_graph(access_token='new_user', persistent_token=False)
        data = facebook.facebook_registration_data()
        assert data['gender'] == 'm'
    
    def test_double_username(self):
        '''
        This used to give an error with duplicate usernames with different capitalization
        '''
        facebook = get_facebook_graph(access_token='short_username', persistent_token=False)
        action, user = connect_user(self.request, facebook_graph=facebook)
        user.username = 'Thierry_schellenbach'
        user.save()
        self.request.user = AnonymousUser()
        facebook = get_facebook_graph(access_token='same_username', persistent_token=False)
        action, new_user = connect_user(self.request, facebook_graph=facebook)
        assert user.username != new_user.username and user.id != new_user.id
    
    
class AuthBackend(FacebookTest):
    def test_auth_backend(self):
        backend = FacebookBackend()
        facebook = get_facebook_graph(access_token='new_user', persistent_token=False)
        action, user = connect_user(self.request, facebook_graph=facebook)
        facebook_email = user.email
        facebook_id = user.get_profile().facebook_id
        auth_user = backend.authenticate(facebook_email=facebook_email)
        assert auth_user == user
        
        auth_user = backend.authenticate(facebook_id=facebook_id)
        assert auth_user == user
        
        auth_user = backend.authenticate(facebook_id=facebook_id, facebook_email=facebook_email)
        assert auth_user == user
        
        auth_user = backend.authenticate()
        assert not auth_user
      
class RequestTest(FacebookTest):
    def test_json_request(self):
        from django_facebook.official_sdk import _request_json
        data = r'''
            {"website": "http://fernandaferrervazquez.blogspot.com/\r\nhttp://twitter.com/fferrervazquez\r\nhttp://comunidad.redfashion.es/profile/fernandaferrervazquez\r\nhttp://www.facebook.com/group.php?gid3D40257259997&ref3Dts\r\nhttp://fernandaferrervazquez.spaces.live.com/blog/cns!EDCBAC31EE9D9A0C!326.trak\r\nhttp://www.linkedin.com/myprofile?trk3Dhb_pro\r\nhttp://www.youtube.com/account#profile\r\nhttp://www.flickr.com/\r\n Mi galer\u00eda\r\nhttp://www.flickr.com/photos/wwwfernandaferrervazquez-showroomrecoletacom/ \r\n\r\nhttp://www.facebook.com/pages/Buenos-Aires-Argentina/Fernanda-F-Showroom-Recoleta/200218353804?ref3Dts\r\nhttp://fernandaferrervazquez.wordpress.com/wp-admin/", "last_name": "Ferrer Vazquez", "locale": "es_LA", "hometown": {"id": "109238842431095", "name": "La Coru\u00f1a, Galicia, Spain"}, "image": "https://graph.facebook.com/me/picture?type3Dlarge&access_token3D100314226679773|2.1ZkFz1Cusu5RlY1xGft_Pg__.86400.1303534800.4-1157872766|ZgsRrRYwp2pqHEHtncqS5-rBiSg"
            , "timezone": -3, "education": [{"school": {"id": "115805661780893", "name": "uba arquitectura dise\u00f1o y urbanismo"}, "classes": [{"description": "direccion de arte", "id": "188729917815843", "name": "AAAP"}, {"with": [{"id": "546455670", "name": "Gustavo Lento"}], "id": "200142039998266", "name": "Indumentaria"}, {"description": "dise\u00f1o ", "with": [{"id": "1285841477", "name": "La Maison Madrid"}], "id": "102056769875267", "name": "figurin"}, {"id": "194463713907701", "name": "indumentaria -figurin-seriado"}, {"with": [{"id": "704003068", "name": "Mariano Toledo"}], "id": "180792848632395", "name": "indumentaria-figurin -seriado.etc"}], "type": "College", "concentration": [{"id": "176664472378719", "name": "indumentaria y dise\u00f1o textil"}]}, {"school": {"id": "107827585907242", "name": "Miami International University of Art & Design"}, "classes": [{"id": "116042535136769", "name": "whadrove asesory"}], "type": "Graduate School", "concentration": [{"id": "146715355391868", "name": "producer-  stylist -  asesora de imagen -personal-shooper -whadrove asesory"}]}, {"school": {"id": "105548239478812", "name": "New York Institute of Technology"}, "classes": [{"id": "199608053396849", "name": "Reporter, Producer and Director"}, {"id": "209828275699578", "name": "personal shooper"}, {"id": "208913322452336", "name": "Designer-stylisti"}], "type": "College", "concentration": [{"id": "184808144897752", "name": "whadrobing"}]}, {"school": {"id": "106431826058746", "name": "Colegio Nuestra Se\u00f1ora de la Misericordia"}, "type": "High School"}, {"school": {"id": "106011862771707", "name": "Mary E. Graham"}, "type": "High School"}, {"school": {"id": "106011862771707", "name": "Mary E. Graham"}, "type": "High School"}], "id": "1157872766", "first_name": "Fernanda", "verified": true, "languages": [{"id": "111021838921932", "name": "Espa\u00f1ol"}, {"id": "110867825605119", "name": "Ingles"}, {"id": "108083115891989", "name": "Portugu\u00e9s"}, {"id": "113051562042989", "name": "Italiano"}], "location": {"id": "106423786059675", "name": "Buenos Aires, Argentina"}, "image_thumb": "https://graph.facebook.com/me/picture?access_token3D100314226679773|2.1ZkFz1Cusu5RlY1xGft_Pg__.86400.1303534800.4-1157872766|ZgsRrRYwp2pqHEHtncqS5-rBiSg", "email": "fer-fer-666@hotmail.com", "username": "FernandaFerrerVazquez", "bio": "ATELIER : TODOS LOS DIAS DE 14 A 22 HS C CITA PREVIA. MIX DE ESTETICAS - ECLECTICA - PRENDAS UNICAS-HAND MADE- SEASSON LESS RETROMODERNIDAD -CUSTOMIZADO !!!\r\n\r\nMe encanta todo el proceso que lleva lograr un objeto que sea unico....personalizarlo de acuerdo a cada uno...a cada persona....a su forma de ser.......elegir los materiales, los avios, las telas...siendo la premisa DIFERENCIARSE!!!!\r\n Atemporal..Retro modernidad...Eclecticismo!!!", "birthday": "04/09/1973", "link": "http://www.facebook.com/FernandaFerrerVazquez", "name": "Fernanda Ferrer Vazquez", "gender": "female", "work": [{"description": "ATELIER : un mix de esteticas que la hacen eclectica, multicultural, excentrica, customizada, artesanal, unica , exclusiva, lujosa, eco-reciclada,con bordados a mano y texturas..especial atencion a los peque\u00f1os detalles!!!! \nSeason less \nHand made ", "employer": {"id": "113960871952651", "name": "fernanda ferrer vazquez"}, "location": {"id": "106423786059675", "name": "Buenos Aires, Argentina"}, "position": {"id": "145270362165639", "name": "Dise\u00f1adora"}, "start_date": "2008-12", "projects": [{"description": "produccion-estilismo-fotografia-make up-pelo-asesoramiento de imagen-whadrobing-perso\u00f1an shooper-rent an outfit!!", "id": "200218353804", "name": "Fernanda F -Showroom Recoleta"}]}, {"employer": {"id": "198034683561689", "name": "el atelier de la isla"}}], "updated_time": "2011-04-22T04:28:27+0000"}
        '''
        from StringIO import StringIO
        file_like = StringIO(data)
        
        user_data = _request_json('test', test_file=file_like)
        school_name_unicode = user_data['education'][0]['school']['name']
        assert isinstance(school_name_unicode, unicode)      
        assert '?' in school_name_unicode.encode('ascii', 'replace')
        
    
class FQLTest(FacebookTest):
    def test_graph_fql(self):
        from django_facebook.api import get_app_access_token
        token = get_app_access_token()
        facebook = get_facebook_graph(access_token=token, persistent_token=False)
        query = 'SELECT name FROM user WHERE uid = me()'
        result = facebook.fql(query)
        assert result == []
    
    def test_fql(self):
        from django_facebook.official_sdk import fql
        query = 'SELECT name FROM user WHERE uid = me()'
        result = fql(query)
        assert not result
    
class SDKTest(FacebookTest):
    def test_photo_put(self):
        from django_facebook.api import get_app_access_token
        token = get_app_access_token()
        graph = get_facebook_graph(access_token=token, persistent_token=False)
        tags = simplejson.dumps([{'x':50, 'y':50, 'tag_uid':12345}, {'x':10, 'y':60, 'tag_text':'a turtle'}])
        try:
            graph.put_photo('img.jpg', 'Look at this cool photo!', None, tags=tags)
        except GraphAPIError, e:
            assert 'An active access token must be used to query information' in unicode(e)
    

    
class DataTransformTest(FacebookTest):
    def test_doctest_api(self):
        return
        #TODO: fix this test somehow, doctest api seems to not work as I expect it
        #tests dont get run
        from django_facebook import api
        import doctest
        tests, failures = doctest.testmod(api)
        assert tests
        assert not failures





if __name__ == '__main__':
    
    unittest.main()

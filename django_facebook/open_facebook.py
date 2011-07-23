'''
Alpha/Testing code....

A generic Facebook API

- Which actually is supported and updated
- Tested so people can contribute smoothly
- Exceptions
- Logging for debugging
'''

import logging
logger = logging.getLogger(__name__)

class OpenFacebookException(Exception):
    pass



class OpenFacebook(object):
    '''
    How will we handle the access token?
    
    Response parsing is weird, sometimes json, sometimes plain string...
    '''
    
    def request(self):
        pass
    
    def request_json(self):
        pass
    
    


from django.utils import simplejson




def base64_url_decode_php_style(inp):
    '''
    PHP follows a slightly different protocol for base64 url decode.
    For a full explanation see:
    http://stackoverflow.com/questions/3302946/how-to-base64-url-decode-in-python
    and
    http://sunilarora.org/parsing-signedrequest-parameter-in-python-bas
    '''
    import base64
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "=" * padding_factor 
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))


def encode_params(params_dict):
    '''
    Take the dictionary of params and encode keys and values to ascii if it's unicode
    '''
    encoded = [(encode_unicode(k), encode_unicode(v)) for k, v in params_dict.items()]
    encoded_dict = dict(encoded)
    return encoded_dict

def encode_unicode(unicode_string):
    if hasattr(unicode_string, 'encode'):
        return unicode_string.encode()
    else:
        return unicode_string


try:
    from django.utils import simplejson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json




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
    encoded = [(smart_str(k), smart_str(v)) for k, v in params_dict.items()]
    encoded_dict = dict(encoded)
    return encoded_dict



def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Adapted from django, needed for urlencoding
    
    Returns a bytestring version of 's', encoded as specified in 'encoding'.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    import types
    if strings_only and isinstance(s, (types.NoneType, int)):
        return s
    elif not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return ' '.join([smart_str(arg, encoding, strings_only,
                        errors) for arg in s])
            return unicode(s).encode(encoding, errors)
    elif isinstance(s, unicode):
        return s.encode(encoding, errors)
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s


try:
    from django.utils import simplejson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json

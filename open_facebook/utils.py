import logging
import re
import sys

logger = logging.getLogger(__name__)
URL_PARAM_RE = re.compile('(?P<k>[^(=|&)]+)=(?P<v>[^&]+)(&|$)')
URL_PARAM_NO_VALUE_RE = re.compile('(?P<k>[^(&|?)]+)(&|$)')


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
    return base64.b64decode(unicode(inp).translate(
        dict(zip(map(ord, u'-_'), u'+/'))))


def encode_params(params_dict):
    '''
    Take the dictionary of params and encode keys and
    values to ascii if it's unicode
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


def send_warning(message, request=None, e=None, **extra_data):
    '''
    Uses the logging system to send a message to logging and sentry
    '''
    username = None
    if request and request.user.is_authenticated():
        username = request.user.username

    error_message = None
    if e:
        error_message = unicode(e)

    data = {
         'username': username,
         'body': error_message,
    }
    data.update(extra_data)
    logger.warn(message,
        exc_info=sys.exc_info(), extra={
        'request': request,
        'data': data
    })


def merge_urls(generated_url, human_url):
    '''
    merge the generated_url with the human_url following this rules:
    params introduced by generated_url are kept
    final params order comes from generated_url
    there's an hack to support things like this http://url?param&param=value

     >>> gen = "http://mysite.com?p1=a&p2=b&p3=c&p4=d"
     >>> hum = "http://mysite.com?p4=D&p3=C&p2=B"
     >>> merge_urls(gen, hum)
     u'http://mysite.com?p1=a&p2=B&p3=C&p4=D'

     >>> gen = "http://mysite.com?id=a&id_s=b&p_id=d"
     >>> hum = "http://mysite.com?id=A&id_s=B&p_id=D"
     >>> merge_urls(gen, hum)
     u'http://mysite.com?id=A&id_s=B&p_id=D'

     >>> gen = "http://mysite.com?p1=a&p2=b&p3=c&p4=d"
     >>> hum = "http://mysite.com"
     >>> merge_urls(gen, hum)
     u'http://mysite.com'

    >>> gen = "http://ad.zanox.com/ppc/?18595160C2000463397T&zpar4=scrapbook&zpar0=e2494344_c4385641&zpar1=not_authenticated&zpar2=unknown_campaign&zpar3=unknown_ref&ULP=http://www.asos.com/ASOS/ASOS-MARS-Loafer-Shoes/Prod/pgeproduct.aspx?iid=1703516&cid=4172&sh=0&pge=2&pgesize=20&sort=-1&clr=Black&affId=2441"
    >>> hum = "http://ad.zanox.com/ppc/?18595160C2000463397T&zpar3=scrapbook&ULP=http://www.asos.com/ASOS/ASOS-MARS-Loafer-Shoes/Prod/pgeproduct.aspx?iid=1703516&cid=4172&sh=0&pge=2&pgesize=20&sort=-1&clr=Black&affId=2441"
    >>> merge_urls(gen, hum)
    u'http://ad.zanox.com/ppc/?18595160C2000463397T&zpar4=scrapbook&zpar0=e2494344_c4385641&zpar1=not_authenticated&zpar2=unknown_campaign&zpar3=scrapbook&ULP=http://www.asos.com/ASOS/ASOS-MARS-Loafer-Shoes/Prod/pgeproduct.aspx?iid=1703516&cid=4172&sh=0&pge=2&pgesize=20&sort=-1&clr=Black&affId=2441'

    >>> gen = "http://mysite.com?invalidparam&p=2"
    >>> hum = "http://mysite.com?p=1"
    >>> merge_urls(gen, hum)
    u'http://mysite.com?invalidparam&p=1'
    '''
    if '?' not in human_url:
        return u'%s' % human_url

    gen_path, gen_args = generated_url.split('?', 1)
    hum_path, hum_args = human_url.split('?', 1)

    get_args = lambda args: [(m.group('k'), m.group('v'))
                             for m in URL_PARAM_RE.finditer(args)]
    get_novalues_args = lambda args: [m.group('k')
                                      for m in URL_PARAM_NO_VALUE_RE.finditer(
                                          args) if "=" not in m.group('k')]

    hum_dict = dict(get_args(hum_args))

    out_args = []

    # prepend crazy param w/o values
    for param in get_novalues_args(gen_args):
        out_args.append(u'%s' % param)

    # replace gen url params
    for k, v in get_args(gen_args):
        out_args.append(u'%s=%s' % (k, hum_dict.get(k, v)))

    return u'%s?%s' % (gen_path, '&'.join(out_args))

from django_facebook.utils import compatible_datetime as datetime
import logging
from open_facebook import exceptions as facebook_exceptions
import sys
logger = logging.getLogger(__name__)


class BaseFacebookInvite(object):

    '''
    An object wrapping some meta data about a facebook invite.
    Use subclasses of this object to splittest different invite messages and see which one works best.
    '''
    type = 'original'
    default_message = "Have you seen my profile on Fashiolista yet? It's full of my latest loves, fabulous fashion finds and other cravings."
    caption = 'Discover, save & share the greatest fashion finds from anywhere on the web!'
    picture = 'http://e.fashiocdn.com/images/logo_facebook_3.png'
    link_format = 'http://www.fashiolista.com/intro_wide/?utm_campaign=invite_flow_%s&utm_medium=invite_flow&utm_source=facebook&fuid=%s'
    name = 'FASHIOLISTA'
    description = None

    @classmethod
    def get_type(cls, invite_message):
        '''
        We allow users to overwrite the default message
        '''
        type = cls.type
        if invite_message != cls.default_message:
            type += '_custom'
        return type

    def get_picture(self, user):
        return getattr(self, 'picture', None)

    def get_link(self, type, user):
        link = self.link_format % (type, user.id)
        return link

    def set_message(self, user, fb, facebook_id, invite_message=None):
        message = invite_message or self.default_message
        kwargs = {}
        picture = self.get_picture(user)
        if picture:
            kwargs['picture'] = picture

        if self.description:
            kwargs['description'] = self.description

        type = self.get_type(invite_message)
        link = self.get_link(type, user)

        wall_post_id = fb.set('%s/feed' % facebook_id, message=message,
                              link=link, name=self.name, caption=self.caption, **kwargs)

        return wall_post_id


def post_on_profile(user, fb, facebook_id, invite_message, force_class=None, force_send=False, raise_=False):
    '''
    Utility function for posting on a users profile.
    Stores the invite in a FacebookInvite model so we can
    - get statistics
    - retry later if the invite failed
    '''
    facebook_classes = [BaseFacebookInvite]
    class_dict = dict([(f.type, f) for f in facebook_classes])
    from django_facebook.models import FacebookInvite
    wallpost_id = None

    try:
        fb_invite, created = FacebookInvite.objects.get_or_create(
            user=user, user_invited=facebook_id, defaults=dict(message=invite_message))
        fb_invite.last_attempt = datetime.now()
        modulo = fb_invite.id % len(facebook_classes)
        message_class = facebook_classes[modulo]
        if force_class:
            message_class = class_dict[force_class]

        if created or force_send:
            # set a different type per style of the message and add custom if
            # there is a custom invite message
            fb_invite.type = message_class.get_type(invite_message)
            fb_invite.save()
            message_instance = message_class()
            wallpost_response = message_instance.set_message(
                user, fb, facebook_id, invite_message)
            wallpost_id = wallpost_response.get('id')
            logger.info(
                'wrote message %s to user %s', invite_message, facebook_id)
            fb_invite.error = False
            fb_invite.error_message = None
            fb_invite.save()
        else:
            logger.info(
                'we are not sending email at the moment cause the invite already existed')
    except facebook_exceptions.OpenFacebookException, e:
        logger.warn(unicode(e), exc_info=sys.exc_info(), extra={
            'data': {
                'user': user,
                'message': invite_message,
                'facebook_user': facebook_id,
                'body': unicode(e),
            }
        })
        fb_invite.error = True
        fb_invite.error_message = unicode(e)
        fb_invite.save()
        if raise_:
            raise

    fb_invite.wallpost_id = wallpost_id
    fb_invite.save()

    return fb_invite

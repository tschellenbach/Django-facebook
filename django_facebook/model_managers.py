from django.db.models.query_utils import Q
from django.core.cache import cache
from django.db import models
import operator
import random
from datetime import timedelta
from django_facebook.utils import compatible_datetime as datetime
from django.contrib.contenttypes.models import ContentType
import logging
from open_facebook.exceptions import OAuthException, UnsupportedDeleteRequest
logger = logging.getLogger(__name__)


class FacebookUserManager(models.Manager):

    def find_users(self, queries, base_queryset=None):
        '''
        Queries, a list of search queries
        Base Queryset, the base queryset in which we are searching
        '''
        if base_queryset is None:
            base_queryset = self.all()
        filters = []
        for query in queries:
            match = Q(
                name__istartswith=query) | Q(name__icontains=' %s' % query)
            filters.append(match)

        users = base_queryset.filter(reduce(operator.and_, filters))

        return users

    def random_facebook_friends(self, user, gender=None, limit=3):
        '''
        Returns a random sample of your FB friends

        Limit = Number of friends
        Gender = None, M or F
        '''
        assert gender in (
            None, 'M', 'F'), 'Gender %s wasnt recognized' % gender

        from django_facebook.utils import get_profile_model
        facebook_cache_key = 'facebook_users_%s' % user.id
        non_members = cache.get(facebook_cache_key)
        profile_class = get_profile_model()
        if not non_members:
            facebook_users = list(
                self.filter(user_id=user.id, gender=gender)[:50])
            facebook_ids = [u.facebook_id for u in facebook_users]
            members = list(profile_class.objects.filter(
                facebook_id__in=facebook_ids).select_related('user'))
            member_ids = [p.facebook_id for p in members]
            non_members = [
                u for u in facebook_users if u.facebook_id not in member_ids]

            cache.set(facebook_cache_key, non_members, 60 * 60)

        random_limit = min(len(non_members), 3)
        random_facebook_users = []
        if random_limit:
            random_facebook_users = random.sample(non_members, random_limit)

        return random_facebook_users


class OpenGraphShareManager(models.Manager):

    def failed(self):
        qs = self.filter(completed_at__isnull=True)
        return qs

    def recently_failed(self):
        from django_facebook import settings as facebook_settings
        now = datetime.now()
        recent_delta = timedelta(
            days=facebook_settings.FACEBOOK_OG_SHARE_RETRY_DAYS)
        recent = now - recent_delta
        failed = self.failed()
        recently_failed = failed.filter(created_at__gte=recent)
        return recently_failed

    def shares_for_instance(self, instance, user):
        content_type = ContentType.objects.get_for_model(instance)
        shares = self.filter(
            user=user,
            object_id=instance.id,
            content_type=content_type,
            completed_at__isnull=False,
            removed_at__isnull=True,
        )
        return shares

    def remove_shares_for_instance(self, content_object, user):
        '''
        Removes all shares for this content_object and user combination
        '''
        shares = self.shares_for_instance(content_object, user)
        shares = shares.filter(
            completed_at__isnull=False, removed_at__isnull=True)
        shares = list(shares[:1000])
        logger.info('found %s shares to remove', len(shares))
        for share in shares:
            logger.info('removed share %s', share)
            try:
                share.remove()
            except (OAuthException, UnsupportedDeleteRequest), e:
                # oauth exceptions happen when tokens are removed
                # unsupported delete requests when the resource is already
                # removed
                logger.info('removing share failed, got error %s', e)

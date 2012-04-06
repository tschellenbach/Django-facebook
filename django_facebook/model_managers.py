from django.db.models.query_utils import Q
from django.core.cache import cache
from django.db import models
import operator
import random




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
            match = Q(name__istartswith=query) | Q(name__icontains=' %s' % query)
            filters.append(match)
                
        users = base_queryset.filter(reduce(operator.and_, filters))

        return users
    
    def random_facebook_friends(self, user, gender=None, limit=3):
        '''
        Returns a random sample of your FB friends
        
        Limit = Number of friends
        Gender = None, M or F 
        '''
        assert gender in (None, 'M', 'F'), 'Gender %s wasnt recognized' % gender
        
        from django_facebook.utils import get_profile_class
        facebook_cache_key = 'facebook_users_%s' % user.id
        non_members = cache.get(facebook_cache_key)
        profile_class = get_profile_class()
        if not non_members:
            facebook_users = list(self.filter(user_id=user.id, gender=gender)[:50])
            facebook_ids = [u.facebook_id for u in facebook_users]
            members = list(profile_class.objects.filter(facebook_id__in=facebook_ids).select_related('user'))
            member_ids = [p.facebook_id for p in members]
            non_members = [u for u in facebook_users if u.facebook_id not in member_ids]
            
            cache.set(facebook_cache_key, non_members, 60*60)
            
        random_limit = min(len(non_members), 3)
        random_facebook_users = []
        if random_limit:
            random_facebook_users = random.sample(non_members, limit)
            
        return random_facebook_users
        
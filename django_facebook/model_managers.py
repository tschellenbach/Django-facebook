from django.db.models.query_utils import Q
from django.db import models
import operator




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
            filters.append(Q(name__icontains=query))
                
        users = base_queryset.filter(reduce(operator.and_, filters))

        return users
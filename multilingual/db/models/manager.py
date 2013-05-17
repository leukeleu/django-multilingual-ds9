"""
Manager for multilingual models
"""
from django.db.models import Manager

from multilingual.db.models.query import MultilingualQuerySet


class MultilingualManager(Manager):
    """
    A manager for multilingual models.
    """
    #TODO: turn this into a proxy manager that would allow developers
    # to use any manager they need.  It should be sufficient to extend
    # and additionaly filter or order querysets returned by that manager.
    def get_query_set(self):
        return MultilingualQuerySet(self.model)

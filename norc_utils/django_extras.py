
"""Utilities that extend Django functionality."""

import itertools

from django.db.models import Manager

# Replaced in Django 1.2 by QuerySet.exists()
def queryset_exists(q):
    """Efficiently tests whether a queryset is empty or not."""
    try:
        q[0]
        return True
    except IndexError:
        return False

def get_object(model, **kwargs):
    """Retrieves a database object of the given class and attributes.
    
    model is the class of the object to find.
    kwargs are the parameters used to find the object.
    If no object is found, returns None.
    
    """
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None

def update_obj(obj):
    return type(obj).objects.get(pk=obj.pk)

class QuerySetManager(Manager):
    """
    
    This Manager uses a QuerySet class defined within its model and
    will forward attribute requests to it so you only have to
    define custom attributes in one place.
    
    """
    use_for_related_fields = True
    
    def get_query_set(self):
        """Use the model.QuerySet class."""
        return self.model.QuerySet(self.model)
    
    def __getattr__(self, attr, *args):
        """Forward attribute lookup to the QuerySet."""
        return getattr(self.get_query_set(), attr, *args)
    

class MultiQuerySet(object):
    
    def __init__(self, *args):
        self.querysets = args
    
    def count(self):
        return sum(qs.count() for qs in self.querysets)
    
    def __len__(self):
        return self.count()
    
    def __getitem__(self, item):
        indices = (offset, stop, step) = item.indices(self.count())
        items = []
        total_len = stop - offset
        for qs in self.querysets:
            if len(qs) < offset:
                offset -= len(qs)
            else:
                items += list(qs[offset:stop])
                if len(items) >= total_len:
                    return items
                else:
                    offset = 0
                    stop = total_len - len(items)
                    continue
    
    def __iter__(self):
        return itertools.chain(*self.querysets)
    
    def __call__(self, *args, **kwargs):
        """Call each queryset."""
        return MultiQuerySet(*[qs(*args, **kwargs) for qs in self.querysets])
    
    def __getattr__(self, attr, *args):
        """Get the attribute for each queryset."""
        return MultiQuerySet(*[getattr(qs, attr, *args)
            for qs in self.querysets])
    

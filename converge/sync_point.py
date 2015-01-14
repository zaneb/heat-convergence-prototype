import functools
import logging

from .framework import datastore


logger = logging.getLogger('sync_point')

sync_points = datastore.Datastore('SyncPoint',
                                  'key', 'waiting', 'satisfied', 'stack_key')

KEY_SEPARATOR = ':'


def _dump_list(items, separator=', '):
    return separator.join(map(str, items))


def make_key(*components):
    assert len(components) >= 2
    return _dump_list(components, KEY_SEPARATOR)


def create(key, predecessors, stack_key):
    sync_points.create_with_key(key, waiting=predecessors,
                                satisfied={}, stack_key=stack_key)


def sync(key, propagate, target, predecessors, new_data):
    sync_point = sync_points.read(key)
    satisfied = dict(sync_point.satisfied)
    satisfied.update(new_data)
    waiting = (predecessors | sync_point.waiting) - set(satisfied)

    # Note: update must be atomic
    sync_points.update(key, waiting=waiting,
                       satisfied=satisfied)

    if waiting:
        logger.debug('[%s] Waiting %s: Got %s; still need %s',
                     key, target, _dump_list(satisfied), _dump_list(waiting))
    else:
        logger.debug('[%s] Ready %s: Got %s',
                     key, target, _dump_list(satisfied))
        propagate(target, satisfied)


@functools.total_ordering
class KeyTraversalMatcher(object):
    '''
    Match the traversal ID in a key.

    In practice this will probably be implemented by storing the components of
    the key in separate fields, but for now this will do the trick.
    '''
    def __init__(self, traversal):
        self.traversal = str(traversal)

    @staticmethod
    def _get_traversal_id(key):
        return key.split(KEY_SEPARATOR, 2)[1]

    def __eq__(self, key):
        return self.traversal == self._get_traversal_id(key)

    def __lt__(self, key):
        return self.traversal < self._get_traversal_id(key)


def delete_all(stack_key, traversal):
    '''
    Delete all of the sync points associated with a particular traversal.
    '''
    for sp in list(sync_points.find(stack_key=stack_key,
                                    key=KeyTraversalMatcher(traversal))):
        sync_points.delete(sp)


__all__ = ['make_key', 'sync', 'delete_all']

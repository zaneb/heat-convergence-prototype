import logging

from .framework import datastore


logger = logging.getLogger('sync_point')

sync_points = datastore.Datastore('SyncPoint',
                                  'key', 'waiting', 'satisfied')

KEY_SEPARATOR = ':'


def _dump_list(items, separator=', '):
    return separator.join(map(str, items))


def make_key(*components):
    assert len(components) >= 2
    return _dump_list(components, KEY_SEPARATOR)


def create(key, predecessors):
    sync_points.create_with_key(key, waiting=predecessors,
                                satisfied={})


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


__all__ = ['make_key', 'sync']

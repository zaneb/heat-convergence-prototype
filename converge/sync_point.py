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

def sync(key, propagate, target, predecessors, new_data):
    if set(new_data).issuperset(predecessors):
        logger.debug('[%s] Immediate %s: %s == %s',
                     key, target, set(new_data), predecessors)
        # Cut to the chase
        propagate(target, new_data)
        return

    try:
        sync_point = sync_points.read(key)
    except sync_points.NotFound:
        logger.debug('[%s] Waiting %s: %s != %s',
                     key, target, set(new_data), predecessors)
        sync_points.create_with_key(key, predecessors=predecessors,
                                    satisfied=new_data)
    else:
        satisfied = dict(sync_point.satisfied)
        satisfied.update(new_data)
        predecessors |= sync_point.predecessors
        if set(satisfied).issuperset(predecessors):
            logger.debug('[%s] Ready %s: %s == %s',
                         key, target, set(satisfied), predecessors)
            propagate(target, satisfied)
            sync_points.delete(key)
        else:
            # Note: update must be atomic
            logger.debug('[%s] Waiting s %s: %s != %s',
                         key, target, set(satisfied), predecessors)
            sync_points.update(key, predecessors=predecessors,
                               satisfied=satisfied)


__all__ = ['make_key', 'sync']

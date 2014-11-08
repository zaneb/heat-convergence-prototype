import collections
import copy
import itertools
import logging


__all__ = ['Datastore']

logger = logging.getLogger('store')

_datastores = set([])


def get_datastore(name):
    for ds in _datastores:
        if ds.name == name:
            return ds


class Datastore(object):

    def __new__(cls, *args):
        ds = super(Datastore, cls).__new__(cls)
        _datastores.add(ds)
        return ds

    def __init__(self, name, *fields):
        self.name = name
        self.clear()
        self.DataType = collections.namedtuple(name, fields)

    @staticmethod
    def clear_all():
        for ds in _datastores:
            ds.clear()

    def clear(self):
        self._store = {}
        self.ids = itertools.count()

    def find(self, **kwargs):
        for key, row in self._store.items():
            reference = dict((k, v) for k, v in row._asdict().items()
                                    if k in kwargs)
            if reference == kwargs:
                yield key

    def create_with_key(self, key, **kwargs):
        logger.debug('[%s] Creating %s' % (self.name, key))
        self._store[key] = self.DataType(key, **copy.deepcopy(kwargs))
        return key

    def create(self, **kwargs):
        return self.create_with_key(next(self.ids), **kwargs)

    def read(self, key):
        logger.debug('[%s] Reading %s' % (self.name, key))
        return copy.deepcopy(self._store[key])

    def update(self, key, **kwargs):
        if isinstance(key, self.DataType):
            key = key[0]
        logger.debug('[%s] Updating %s' % (self.name, key))
        self._store[key] = self._store[key]._replace(**copy.deepcopy(kwargs))

    def delete(self, key):
        if isinstance(key, self.DataType):
            key = key[0]
        logger.debug('[%s] Deleting %s' % (self.name, key))
        del self._store[key]

    @property
    def keys(self):
        return self._store.keys()

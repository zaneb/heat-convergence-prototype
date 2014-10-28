import logging
import uuid

from .framework import datastore


logger = logging.getLogger('rsrcs')


resources = datastore.Datastore('Resource',
                                'key', 'stack_key', 'name', 'phys_id')


class Resource(object):
    def __init__(self, name, stack, defn, phys_id=None,
                 key=None):
        self.key = key
        self.name = name
        self.stack = stack
        self.defn = defn
        self.physical_resource_id = phys_id

    @classmethod
    def _load_from_store(cls, key, get_stack):
        loaded = resources.read(key)
        return cls(loaded.name, get_stack(loaded.stack_key),
                   None,
                   loaded.phys_id,
                   loaded.key)

    @classmethod
    def load(cls, key):
        from . import stack

        return cls._load_from_store(key, stack.Stack.load)

    @classmethod
    def load_all_from_stack(cls, stack):
        stored = resources.find(stack_key=stack.key)
        return (cls._load_from_store(key, lambda sk: stack) for key in stored)

    def store(self):
        data = {
            'name': self.name,
            'stack_key': self.stack.key,
            'phys_id': self.physical_resource_id,
        }

        if self.key is None:
            self.key = resources.create(**data)
        else:
            resources.update(self.key, **data)

    def create(self):
        self.physical_resource_id = str(uuid.uuid4())
        logger.info('[%s(%d)] Created %s' % (self.name,
                                             self.key,
                                             self.physical_resource_id))
        self.store()

    def delete(self):
        logger.info('[%s(%d)] Deleted' % (self.name, self.key))
        resources.delete(self.key)

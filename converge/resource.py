import collections
import logging
import uuid

from .framework import datastore


logger = logging.getLogger('rsrcs')

GraphKey = collections.namedtuple('GraphKey', ['name', 'key', 'forward'])

resources = datastore.Datastore('Resource',
                                'key', 'stack_key', 'name', 'template_key',
                                'props_data', 'phys_id')


class UpdateReplace(Exception):
    pass


class Resource(object):
    def __init__(self, name, stack, defn, template_key=None,
                 props_data=None, phys_id=None,
                 key=None):
        self.key = key
        self.name = name
        self.stack = stack
        self.defn = defn
        self.template_key = template_key
        self.props_data = props_data
        self.physical_resource_id = phys_id

    @classmethod
    def _load_from_store(cls, key, get_stack):
        loaded = resources.read(key)
        return cls(loaded.name, get_stack(loaded.stack_key),
                   None,
                   loaded.template_key,
                   loaded.props_data,
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

    def graph_key(self, forward=True):
        return GraphKey(self.name, self.key, forward)

    def store(self):
        data = {
            'name': self.name,
            'stack_key': self.stack.key,
            'template_key': self.template_key,
            'phys_id': self.physical_resource_id,
            'props_data': self.props_data,
        }

        if self.key is None:
            self.key = resources.create(**data)
        else:
            resources.update(self.key, **data)

    def refid(self):
        return self.physical_resource_id

    def attributes(self):
        # Just mirror properties -> attributes for test purposes
        return self.props_data

    def create(self, template_key, resource_ids, resource_attrs):
        self.physical_resource_id = self.name + "_phys_id"  # predictable phys_id for test purposes
        self.template_key = template_key
        self.props_data = self.defn.resolved_props(resource_ids,
                                                   resource_attrs)
        logger.info('[%s(%d)] Created %s' % (self.name,
                                             self.key,
                                             self.physical_resource_id))
        logger.info('[%s(%d)] Properties: %s' % (self.name,
                                                 self.key,
                                                 self.props_data))
        self.store()

    def update(self, template_key, resource_ids, resource_attrs):
        new_props_data = self.defn.resolved_props(resource_ids,
                                                  resource_attrs)
        for key, val in new_props_data.items():
            if val != self.props_data[key] and '!' in key:
                logger.info('[%s(%d)] Needs replacement' % (self.name,
                                                            self.key))
                raise UpdateReplace

        logger.info('[%s(%d)] Updating in place' % (self.name,
                                                    self.key))
        self.template_key = template_key
        self.props_data = new_props_data
        logger.info('[%s(%d)] Properties: %s' % (self.name,
                                                 self.key,
                                                 self.props_data))
        self.store()

    def delete(self):
        logger.info('[%s(%d)] Deleted %s' % (self.name,
                                             self.key,
                                             self.physical_resource_id))
        resources.delete(self.key)

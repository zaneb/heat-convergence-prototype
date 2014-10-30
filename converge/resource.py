import collections
import logging

from .framework import datastore
from . import reality


logger = logging.getLogger('rsrcs')

GraphKey = collections.namedtuple('GraphKey', ['name', 'key'])
InputData = collections.namedtuple('InputData', ['key', 'refid', 'attrs'])

resources = datastore.Datastore('Resource',
                                'key', 'stack_key', 'name', 'template_key',
                                'requirers', 'requirements',
                                'props_data', 'phys_id')


class Resource(object):
    def __init__(self, name, stack, defn, template_key=None,
                 requirers=[], requirements=[], props_data=None, phys_id=None,
                 key=None):
        self.key = key
        self.name = name
        self.stack = stack
        self.defn = defn
        self.template_key = template_key
        self.requirers = requirers
        self.requirements = requirements
        self.props_data = props_data
        self.physical_resource_id = phys_id

    @classmethod
    def _load_from_store(cls, key, get_stack):
        loaded = resources.read(key)
        return cls(loaded.name, get_stack(loaded.stack_key),
                   None,
                   loaded.template_key,
                   loaded.requirers,
                   loaded.requirements,
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
            'requirers': self.requirers,
            'requirements': self.requirements,
            'props_data': self.props_data,
            'phys_id': self.physical_resource_id,
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

    def create(self, template_key, resource_data):
        self.template_key = template_key
        self.requirements = [d.key for d in resource_data.values()]
        self.props_data = self.defn.resolved_props(resource_data)

        uuid = reality.reality.create_resource(self.name, self.props_data)
        self.physical_resource_id = uuid
        logger.info('[%s(%d)] Created %s' % (self.name,
                                             self.key,
                                             self.physical_resource_id))
        logger.info('[%s(%d)] Properties: %s' % (self.name,
                                                 self.key,
                                                 self.props_data))
        self.store()

    def delete(self):
        reality.reality.delete_resource(self.physical_resource_id)
        logger.info('[%s(%d)] Deleted %s' % (self.name,
                                             self.key,
                                             self.physical_resource_id))
        resources.delete(self.key)

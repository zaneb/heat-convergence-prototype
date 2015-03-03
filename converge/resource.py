import collections
import logging

from .framework import datastore
from . import reality


logger = logging.getLogger('rsrcs')

InputData = collections.namedtuple('InputData', ['key', 'name',
                                                 'refid', 'attrs'])

resources = datastore.Datastore('Resource',
                                'key', 'stack_key', 'name', 'template_key',
                                'requirers', 'requirements',
                                'replaces', 'replaced_by',
                                'props_data', 'phys_id',
                                'status')


STATUSES = (COMPLETE, IN_PROGRESS) = ('COMPLETE', 'IN_PROGRESS')


class UpdateReplace(Exception):
    pass


class UpdateInProgress(Exception):
    pass


class Resource(object):
    '''
    Class to represent a Resource.

    This is the equivalent of the heat.engine.resource.Resource class in this
    simulation.
    '''
    def __init__(self, name, stack, defn, template_key=None,
                 requirers=set(), requirements=set(),
                 replaces=None, replaced_by=None,
                 props_data=None, phys_id=None,
                 status=COMPLETE,
                 key=None):
        self.key = key
        self.name = name
        self.stack = stack
        self.defn = defn
        self.template_key = template_key
        self.requirers = requirers
        self.requirements = requirements
        self.replaces = replaces
        self.replaced_by = replaced_by
        self.props_data = props_data
        self.physical_resource_id = phys_id
        self.status = status

    @classmethod
    def _load_from_store(cls, key, get_stack):
        loaded = resources.read(key)
        return cls(loaded.name, get_stack(loaded.stack_key),
                   None,
                   loaded.template_key,
                   loaded.requirers,
                   loaded.requirements,
                   loaded.replaces,
                   loaded.replaced_by,
                   loaded.props_data,
                   loaded.phys_id,
                   loaded.status,
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
            'template_key': self.template_key,
            'requirers': self.requirers,
            'requirements': self.requirements,
            'replaces': self.replaces,
            'replaced_by': self.replaced_by,
            'props_data': self.props_data,
            'phys_id': self.physical_resource_id,
            'status': self.status,
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
        self.status = IN_PROGRESS
        self.store()  # Note: must be atomic update

        self.template_key = template_key
        self.requirements = set(d.key for k, d in resource_data.items())
        self.props_data = self.defn.resolved_props(resource_data)

        uuid = reality.reality.create_resource(self.name, self.props_data)
        self.physical_resource_id = uuid
        logger.info('[%s(%d)] Created %s' % (self.name,
                                             self.key,
                                             self.physical_resource_id))
        logger.info('[%s(%d)] Properties: %s' % (self.name,
                                                 self.key,
                                                 self.props_data))
        self.status = COMPLETE
        self.store()

    def update(self, template_key, resource_data):
        new_props_data = self.defn.resolved_props(resource_data)
        new_requirements = set(d.key for k, d in resource_data.items())

        for key, val in new_props_data.items():
            if val != self.props_data[key] and '!' in key:
                logger.info('[%s(%d)] Needs replacement' % (self.name,
                                                            self.key))
                raise UpdateReplace

        if self.status == IN_PROGRESS:
            logger.info('[%s(%d)] Previous update still in progress')
            raise UpdateInProgress

        logger.info('[%s(%d)] Updating in place' % (self.name,
                                                    self.key))
        self.status = IN_PROGRESS
        self.requirements |= new_requirements
        self.store()  # Note: must be atomic update

        self.template_key = template_key
        self.requirements = new_requirements
        self.props_data = new_props_data
        reality.reality.update_resource(self.physical_resource_id,
                                        self.props_data)
        logger.info('[%s(%d)] Properties: %s' % (self.name,
                                                 self.key,
                                                 self.props_data))
        self.status = COMPLETE
        self.store()

    def make_replacement(self, template_key, resource_data):
        rsrc = Resource(self.name, self.stack,
                        self.defn, template_key,
                        requirers=self.requirers, replaces=self.key)
        rsrc.store()

        self.replaced_by = rsrc.key
        self.store()

        return rsrc

    def clear_requirers(self, gone_requirers):
        self.requirers -= set(gone_requirers)
        self.store()

    def delete(self):
        if self.status == IN_PROGRESS:
            logger.info('[%s(%d)] Previous update still in progress')
            raise UpdateInProgress

        self.status = IN_PROGRESS
        self.store()  # Note: must be atomic update

        if self.physical_resource_id is not None:
            reality.reality.delete_resource(self.physical_resource_id)
        logger.info('[%s(%d)] Deleted %s' % (self.name,
                                             self.key,
                                             self.physical_resource_id))
        resources.delete(self.key)
        self.key = None

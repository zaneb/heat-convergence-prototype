import logging

from .framework import datastore
from .framework import process

from . import resource
from . import template


logger = logging.getLogger('converger')

sync_points = datastore.Datastore('SyncPoint',
                                  'key', 'predecessors', 'satisfied')


class Converger(process.MessageProcessor):
    def __init__(self):
        super(Converger, self).__init__('converger')

    @process.asynchronous
    def check_resource(self, resource_key, template_key):
        rsrc = resource.Resource.load(resource_key)
        tmpl = template.Template.load(template_key)

        if rsrc.stack.tmpl.key != template_key:
            logger.debug('[%s] Traversal cancelled; stopping.', template_key)
            return

        if rsrc.physical_resource_id is None:
            rsrc.create(template_key)

        for req in rsrc.requirers:
            req_rsrc = resource.Resource.load(req)
            predecessors = tmpl.resources[req_rsrc.name].dependency_names()
            self.propagate_check_resource(req, template_key,
                                          set(predecessors), rsrc.name)

    def propagate_check_resource(self, next_resource_key, template_key,
                                 predecessors, sender):
        if len(predecessors) == 1:
            # Cut to the chase
            self.check_resource(next_resource_key, template_key)
            return

        key = '%d-%d' % (next_resource_key, template_key)
        try:
            sync_point = sync_points.read(key)
        except KeyError:
            sync_points.create_with_key(key, predecessors=predecessors,
                                        satisfied=[sender])
        else:
            satisfied = sync_point.satisfied + [sender]
            predecessors |= sync_point.predecessors
            if set(satisfied).issuperset(predecessors):
                self.check_resource(next_resource_key, template_key)
                sync_points.delete(key)
            else:
                # Note: update must be atomic
                sync_points.update(key, predecessors=predecessors,
                                   satisfied=satisfied)

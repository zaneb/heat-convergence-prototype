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

    def check_resource_update(self, rsrc, template_key):
        if rsrc.stack.tmpl.key != template_key:
            logger.debug('[%s] Traversal cancelled; stopping.', template_key)
            return False

        rsrc.defn = rsrc.stack.tmpl.resources[rsrc.name]

        # TODO: push instead of querying this data. Clearly this is
        # hideously inefficient.
        graph = rsrc.stack.dependencies().graph()
        loaded = resource.Resource.load_all_from_stack(rsrc.stack)
        resources = [r for r in loaded if r.graph_key() in graph]
        res_ids = {r.name: r.refid() for r in resources}
        res_attrs = {r.name: r.attributes() for r in resources}

        if rsrc.physical_resource_id is None:
            rsrc.create(template_key, res_ids, res_attrs)
        else:
            try:
                rsrc.update(template_key, res_ids, res_attrs)
            except resource.UpdateReplace:
                replacement = rsrc.stack.create_replacement(rsrc.name,
                                                            rsrc.defn,
                                                            rsrc.key)
                replacement.create(template_key, res_ids, res_attrs)

        return True

    def check_resource_cleanup(self, rsrc, template_key):
        if rsrc.template_key != template_key:
            rsrc.delete()

        return True

    @process.asynchronous
    def check_resource(self, resource_key, template_key, forward):
        try:
            rsrc = resource.Resource.load(resource_key)
        except KeyError:
            if not forward:
                return
            else:
                raise

        if forward:
            do_check = self.check_resource_update
        else:
            do_check = self.check_resource_cleanup

        if not do_check(rsrc, template_key):
            return

        deps = rsrc.stack.dependencies()
        graph = deps.graph()

        graph_key = rsrc.graph_key(forward)
        for req in deps.required_by(graph_key):
            self.propagate_check_resource(req, template_key,
                                          set(graph[req]), graph_key)

    def propagate_check_resource(self, next_res_graph_key, template_key,
                                 predecessors, sender):
        if len(predecessors) == 1:
            # Cut to the chase
            self.check_resource(next_res_graph_key.key, template_key,
                                next_res_graph_key.forward)
            return

        key = '%s-%s-%s' % (next_res_graph_key.key,
                            template_key,
                            next_res_graph_key.forward and 'F' or 'R')
        try:
            sync_point = sync_points.read(key)
        except KeyError:
            sync_points.create_with_key(key, predecessors=predecessors,
                                        satisfied=[sender])
        else:
            satisfied = sync_point.satisfied + [sender]
            predecessors |= sync_point.predecessors
            if set(satisfied).issuperset(predecessors):
                self.check_resource(next_res_graph_key.key, template_key,
                                    next_res_graph_key.forward)
                sync_points.delete(key)
            else:
                # Note: update must be atomic
                sync_points.update(key, predecessors=predecessors,
                                   satisfied=satisfied)

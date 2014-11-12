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

    def check_resource_update(self, rsrc, template_key, data):
        rsrc.defn = rsrc.stack.tmpl.resources[rsrc.name]

        if rsrc.physical_resource_id is None:
            rsrc.create(template_key, data)
        else:
            rsrc.update(template_key, data)

    def check_resource_cleanup(self, rsrc, template_key):
        pass

    @process.asynchronous
    def check_resource(self, resource_key, template_key, data, forward):
        rsrc = resource.Resource.load(resource_key.key)
        tmpl = rsrc.stack.tmpl

        if tmpl.key != template_key:
            logger.debug('[%s] Traversal cancelled; stopping.', template_key)
            return

        if forward:
            self.check_resource_update(rsrc, template_key, data)

            tmpl_deps = tmpl.dependencies()
            graph = tmpl_deps.graph()

            input_data = resource.InputData(rsrc.key,
                                            rsrc.refid(), rsrc.attributes())

            self.propagate_check_resource(resource_key,
                                          template_key,
                                          rsrc.requirers | {resource_key},
                                          resource_key, None, False)

            for req in rsrc.requirers:
                defn = tmpl.resources.get(req.name)
                if defn is not None:
                    predecessors = defn.dependency_names()
                    self.propagate_check_resource(req, template_key,
                                                  set(graph[req.name]),
                                                  rsrc.name,
                                                  input_data, True)
        else:
            self.check_resource_cleanup(rsrc, template_key)

            for req in rsrc.requirements:
                # Note that this is pretty inefficient, since it requires each
                # next node to be loaded from the DB in order to determine how
                # many signals they each need to wait for. It may be possible
                # to pregenerate this data at the beginning of the update and
                # pass it down through the RPC messages instead.
                req_rsrc = resource.Resource.load(req)

                req_graph_key = resource.GraphKey(req_rsrc.name, req)
                self.propagate_check_resource(req_graph_key,
                                              template_key,
                                              req_rsrc.requirers,
                                              resource_key, None, False)

    def propagate_check_resource(self, next_res_graph_key, template_key,
                                 predecessors, sender, sender_data, forward):
        if len(predecessors) == 1:
            # Cut to the chase
            self.check_resource(next_res_graph_key, template_key,
                                {sender: sender_data}, forward)
            return

        key = '%s-%s-%s' % (next_res_graph_key.key, template_key,
                            'update' if forward else 'cleanup')
        try:
            sync_point = sync_points.read(key)
        except KeyError:
            sync_points.create_with_key(key, predecessors=predecessors,
                                        satisfied={sender: sender_data})
        else:
            satisfied = dict(sync_point.satisfied)
            satisfied[sender] = sender_data
            predecessors |= sync_point.predecessors
            if set(satisfied).issuperset(predecessors):
                self.check_resource(next_res_graph_key, template_key,
                                    satisfied, forward)
                sync_points.delete(key)
            else:
                # Note: update must be atomic
                sync_points.update(key, predecessors=predecessors,
                                   satisfied=satisfied)

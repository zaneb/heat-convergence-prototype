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

    def check_resource_cleanup(self, rsrc, template_key, data):
        rsrc.clear_requirers(rsrc_key for rsrc_key, key in data.items()
                                    if key is None)

        if rsrc.template_key != template_key:
            rsrc.delete()

    @process.asynchronous
    def check_resource(self, resource_key, template_key, data, cleanup_deps,
                       forward):
        try:
            rsrc = resource.Resource.load(resource_key.key)
        except KeyError:
            return
        tmpl = rsrc.stack.tmpl

        if tmpl.key != template_key:
            logger.debug('[%s] Traversal cancelled; stopping.', template_key)
            return

        cleanup_graph = cleanup_deps.graph()

        if forward:
            if rsrc.replaced_by and rsrc.template_key != template_key:
                return

            try:
                self.check_resource_update(rsrc, template_key, data)
            except resource.UpdateReplace:
                replacement = rsrc.create_replacement(template_key, data)
                self.check_resource(resource.GraphKey(replacement.name,
                                                      replacement.key),
                                    template_key, data, cleanup_deps, True)
                return

            tmpl_deps = tmpl.dependencies()
            graph = tmpl_deps.graph()

            input_data = resource.InputData(rsrc.key,
                                            rsrc.refid(), rsrc.attributes())

            cleanup_node = resource.GraphKey(rsrc.name, rsrc.replaces)
            if rsrc.replaces is not None and cleanup_node in cleanup_graph:
                cleanup_node_key = cleanup_node.key
            else:
                cleanup_node = resource_key
                cleanup_node_key = rsrc.key

            if cleanup_node in cleanup_graph:
                cleanup_requirers = (set(cleanup_graph[cleanup_node]) |
                                        {cleanup_node})
                self.propagate_check_resource(cleanup_node,
                                              template_key,
                                              cleanup_requirers,
                                              cleanup_node, cleanup_node_key,
                                              cleanup_deps, False)

            for req in rsrc.requirers:
                defn = tmpl.resources.get(req.name)
                if defn is not None:
                    predecessors = defn.dependency_names()
                    self.propagate_check_resource(req, template_key,
                                                  set(graph[req.name]),
                                                  rsrc.name,
                                                  input_data,
                                                  cleanup_deps, True)
        else:
            self.check_resource_cleanup(rsrc, template_key, data)

            if resource_key in cleanup_graph:
                for req in cleanup_deps.required_by(resource_key):
                    requirers = set(cleanup_graph[req]) | {resource_key}

                    self.propagate_check_resource(req,
                                                  template_key,
                                                  requirers,
                                                  resource_key, rsrc.key,
                                                  cleanup_deps, False)

    def propagate_check_resource(self, next_res_graph_key, template_key,
                                 predecessors, sender, sender_data,
                                 cleanup_deps, forward):
        if len(predecessors) == 1:
            logger.debug('[%s] Immediate %s %s: %s == %s',
                         template_key,
                         next_res_graph_key,
                         'update' if forward else 'cleanup',
                         sender, predecessors)
            # Cut to the chase
            self.check_resource(next_res_graph_key, template_key,
                                {sender: sender_data}, cleanup_deps, forward)
            return

        key = '%s-%s-%s' % (next_res_graph_key.key, template_key,
                            'update' if forward else 'cleanup')
        try:
            sync_point = sync_points.read(key)
        except KeyError:
            logger.debug('[%s] Waiting %s %s: %s != %s',
                         template_key,
                         next_res_graph_key,
                         'update' if forward else 'cleanup',
                         sender, predecessors)
            sync_points.create_with_key(key, predecessors=predecessors,
                                        satisfied={sender: sender_data})
        else:
            satisfied = dict(sync_point.satisfied)
            satisfied[sender] = sender_data
            predecessors |= sync_point.predecessors
            if set(satisfied).issuperset(predecessors):
                logger.debug('[%s] Ready %s %s: %s == %s',
                             template_key,
                             next_res_graph_key,
                             'update' if forward else 'cleanup',
                             set(satisfied), predecessors)
                self.check_resource(next_res_graph_key, template_key,
                                    satisfied, cleanup_deps, forward)
                sync_points.delete(key)
            else:
                # Note: update must be atomic
                logger.debug('[%s] Waiting %s %s: %s != %s',
                             template_key,
                             next_res_graph_key,
                             'update' if forward else 'cleanup',
                             set(satisfied), predecessors)
                sync_points.update(key, predecessors=predecessors,
                                   satisfied=satisfied)

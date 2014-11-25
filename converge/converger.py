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

        input_data = {key.name: in_data for (key, fwd), in_data in data.items()}

        if rsrc.physical_resource_id is None:
            rsrc.create(template_key, input_data)
        else:
            rsrc.update(template_key, input_data)

    def check_resource_cleanup(self, rsrc, template_key, data):
        rsrc.clear_requirers(rsrc_key for rsrc_key, key in data.items()
                                    if key is None)

        if rsrc.template_key != template_key:
            rsrc.delete()

    @process.asynchronous
    def check_resource(self, resource_key, template_key, data, deps,
                       forward):
        try:
            rsrc = resource.Resource.load(resource_key.key)
        except KeyError:
            return
        tmpl = rsrc.stack.tmpl

        if tmpl.key != template_key:
            logger.debug('[%s] Traversal cancelled; stopping.', template_key)
            return

        graph = deps.graph()

        if forward:
            if rsrc.replaced_by and rsrc.template_key != template_key:
                return

            try:
                self.check_resource_update(rsrc, template_key, data)
            except resource.UpdateReplace:
                replacement = rsrc.create_replacement(template_key, data)
                self.check_resource(resource.GraphKey(replacement.name,
                                                      replacement.key),
                                    template_key, data, deps, True)
                return

            input_data = resource.InputData(rsrc.key,
                                            rsrc.refid(), rsrc.attributes())
        else:
            self.check_resource_cleanup(rsrc, template_key, data)


        graph_key = (resource_key, forward)
        if graph_key not in graph and rsrc.replaces:
            graph_key = (resource.GraphKey(rsrc.name, rsrc.replaces),
                         forward)

        for req, fwd in deps.required_by(graph_key):
            self.propagate_check_resource(req, template_key,
                                          set(graph[(req, fwd)]),
                                          graph_key,
                                          input_data if fwd else rsrc.key,
                                          deps, fwd)

        if forward:
            self.check_stack_complete(rsrc.stack, template_key, resource_key,
                                      graph)

    def check_stack_complete(self, stack, template_key, sender, graph):
        roots = set(key for (key, fwd), node in graph.items()
                        if fwd and not any(f for k, f in node.required_by()))

        if sender not in roots:
            return

        key = '%s-%s' % (stack.key, template_key)

        try:
            sync_point = sync_points.read(key)
        except KeyError:
            sync_points.create_with_key(key, predecessors=roots,
                                        satisfied={sender: None})
        else:
            satisfied = dict(sync_point.satisfied)
            satisfied[sender] = None
            if set(satisfied).issuperset(roots):
                stack.mark_complete(template_key)
                sync_points.delete(key)
            else:
                sync_points.update(key, predecessors=roots,
                                   satisfied=satisfied)

    def propagate_check_resource(self, next_res_graph_key, template_key,
                                 predecessors, sender, sender_data,
                                 deps, forward):
        if len(predecessors) == 1:
            logger.debug('[%s] Immediate %s %s: %s == %s',
                         template_key,
                         next_res_graph_key,
                         'update' if forward else 'cleanup',
                         sender, predecessors)
            # Cut to the chase
            self.check_resource(next_res_graph_key, template_key,
                                {sender: sender_data}, deps, forward)
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
                                    satisfied, deps, forward)
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

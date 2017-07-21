import logging

from .framework import datastore
from .framework import process

from . import dependencies
from . import resource
from . import sync_point
from . import template


logger = logging.getLogger('converger')


class Converger(process.MessageProcessor):
    '''
    The message handler for asynchronous notifications within Heat.
    '''

    def __init__(self):
        super(Converger, self).__init__('converger')

    def check_resource_update(self, rsrc, template_key, data):
        '''
        Create or update the Resource if appropriate.
        '''
        rsrc.defn = rsrc.stack.tmpl.resources[rsrc.name]

        input_data = {in_data.name: in_data for in_data in data.values()}

        if rsrc.physical_resource_id is None:
            rsrc.create(template_key, input_data)
        else:
            rsrc.update(template_key, input_data)

    def check_resource_cleanup(self, rsrc, template_key, data):
        '''
        Delete the Resource if appropriate.
        '''
        if rsrc.template_key != template_key:
            rsrc.delete()

    @process.asynchronous
    def check_resource(self, resource_key, traversal_id, data, forward):
        '''
        Process a node in the dependency graph.

        The node may be associated with either an update or a cleanup of its
        associated resource.
        '''
        try:
            rsrc = resource.Resource.load(resource_key)
        except resource.resources.NotFound:
            return
        tmpl = rsrc.stack.tmpl

        if traversal_id != rsrc.stack.current_traversal:
            logger.debug('[%s] Traversal cancelled; stopping.', traversal_id)
            return

        deps = rsrc.stack.current_deps
        graph = deps.graph()

        if forward:
            if (rsrc.replaced_by is not None and
                    rsrc.template_key != tmpl.key):
                return

            try:
                self.check_resource_update(rsrc, tmpl.key, data)
            except resource.UpdateReplace:
                replacement = rsrc.make_replacement(tmpl.key, data)
                self.check_resource(replacement.key,
                                    traversal_id, data, True)
                return
            except resource.UpdateInProgress:
                return

            # We'll pass on this data so that subsequent resources can update
            # their dependencies and their get_resource and getattr values.
            input_data = resource.InputData(rsrc.key, rsrc.name,
                                            rsrc.refid(), rsrc.attributes())
        else:
            try:
                self.check_resource_cleanup(rsrc, tmpl.key, data)
            except resource.UpdateInProgress:
                return


        graph_key = (resource_key, forward)
        if graph_key not in graph and rsrc.replaces is not None:
            # If we are a replacement, impersonate the replaced resource for
            # the purposes of calculating whether subsequent resources are
            # ready, since everybody has to work from the same version of the
            # graph. Our real resource ID is sent in the input_data, so the
            # dependencies will get updated to point to this resource in time
            # for the next traversal.
            graph_key = (rsrc.replaces, forward)

        try:
            for req, fwd in deps.required_by(graph_key):
                self.propagate_check_resource(req, traversal_id,
                                              set(graph[(req, fwd)]),
                                              graph_key,
                                              input_data if fwd else rsrc.key,
                                              fwd)

            if forward:
                self.check_stack_complete(rsrc.stack, traversal_id,
                                          resource_key, graph)
        except sync_point.sync_points.NotFound:
            # Note: this cannot actually happen in the current test framework
            stack = rsrc.stack.load(rsrc.stack.key)

            key = sync_point.make_key(resource_key, stack.current_traversal,
                                      'update' if forward else 'cleanup')
            def do_check(target_key, data):
                self.check_resource(resource_key, stack.current_traversal,
                                    data)

            try:
                sync_point.sync(key, do_check, resource_key, predecessors,
                                {})
            except sync_point.sync_points.NotFound:
                pass

    def check_stack_complete(self, stack, traversal_id, sender, graph):
        '''
        Mark the stack complete if the update is complete.

        Complete is currently in the sense that all desired resources are in
        service, not that superfluous ones have been cleaned up.
        '''
        roots = set(key for (key, fwd), node in graph.items()
                        if fwd and not any(f for k, f in node.required_by()))

        if sender not in roots:
            return

        key = sync_point.make_key(stack.key, traversal_id)

        def mark_complete(stack_key, data):
            stack.mark_complete(traversal_id)

        sync_point.sync(key, mark_complete, stack.key, roots, {sender: None})

    def propagate_check_resource(self, next_res_graph_key, traversal_id,
                                 predecessors, sender, sender_data, forward):
        '''
        Trigger processing of a node iff all of its dependencies are satisfied.
        '''
        key = sync_point.make_key(next_res_graph_key, traversal_id,
                                  'update' if forward else 'cleanup')

        def do_check(target_key, data):
            self.check_resource(target_key, traversal_id, data, forward)

        sync_point.sync(key, do_check, next_res_graph_key, predecessors,
                        {sender: sender_data})

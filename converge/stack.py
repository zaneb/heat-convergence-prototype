import logging

from .framework import datastore

from . import dependencies
from . import resource
from . import template


logger = logging.getLogger('stack')

stacks = datastore.Datastore('Stack',
                             'key', 'name', 'tmpl_key', 'prev_tmpl_key',
                             'current_traversal')


class Stack(object):
    '''
    Class to represent a Stack.

    This is the equivalent of the heat.engine.stack.Stack class in this
    simulation.
    '''

    def __init__(self, name, tmpl, prev_tmpl_key=None, current_traversal=0,
                 key=None):
        self.key = key
        self.tmpl = tmpl
        self.data = {
            'name': name,
            'tmpl_key': tmpl.key,
            'prev_tmpl_key': prev_tmpl_key,
            'current_traversal': current_traversal,
        }

    def __str__(self):
        return '<Stack %r>' % self.key

    @classmethod
    def load(cls, key):
        s = stacks.read(key)
        return cls(s.name, template.Template.load(s.tmpl_key), s.prev_tmpl_key,
                   s.current_traversal, key=s.key)

    @classmethod
    def load_by_name(cls, stack_name):
        candidates = list(stacks.find(name=stack_name))
        if not candidates:
            raise stacks.NotFound('Stack "%s" not found' % stack_name)
        assert len(candidates) == 1, 'Multiple stacks "%s" found' % stack_name
        return cls.load(candidates[0])

    def store(self):
        if self.key is None:
            self.key = stacks.create(**self.data)
        else:
            stacks.update(self.key, **self.data)

    @property
    def current_traversal(self):
        return self.data['current_traversal']

    def create(self):
        self.store()
        self._create_or_update()

    def update(self, tmpl):
        old_tmpl, self.tmpl = self.tmpl, tmpl
        self.data['tmpl_key'] = tmpl.key

        logger.info('[%s(%d)] Updating...' % (self.data['name'], self.key))
        self._create_or_update(old_tmpl.key)

    @staticmethod
    def _dependencies(existing_resources,
                      current_template_deps, current_resources):
        '''
        Return the Dependencies graph for a traversal.

        There is a node for each resource that appears in the current template
        (to be traversed in the forward direction for updates) and for each
        existing resource (to be traversed in the reverse direction for
        cleanup.
        '''
        def make_graph_key(res_name):
            return (resource.GraphKey(res_name,
                                      current_resources[res_name].key),
                    True)

        deps = current_template_deps.translate(make_graph_key)

        for key, rsrc in existing_resources.items():
            deps += (key, False), None

            # Note: reversed edges as this is the cleanup part of the graph
            for requirement in rsrc.requirements:
                if requirement in existing_resources:
                    deps += (requirement, False), (key, False)
            if rsrc.replaces in existing_resources:
                deps += ((resource.GraphKey(rsrc.name,
                                            rsrc.replaces), False),
                         (key, False))

            if rsrc.name in current_template_deps:
                deps += (key, False), make_graph_key(rsrc.name)

        return deps

    def delete(self):
        old_tmpl, self.tmpl = self.tmpl, template.Template()
        self.data['tmpl_key'] = None

        logger.info('[%s(%d)] Deleting...' % (self.data['name'], self.key))
        self._create_or_update(old_tmpl.key)

    def rollback(self):
        '''
        Roll the Stack back to the previously successful template.

        This essentially performs an update with the most recent template to
        successfully complete (where 'complete' currently means that all
        desired resources are in service, not necessarily that any extras have
        been cleaned up.
        '''
        old_tmpl_key = self.data['prev_tmpl_key']
        if old_tmpl_key == self.tmpl.key:
            # Nothing to roll back
            return

        if old_tmpl_key is None:
            self.tmpl = template.Template()
        else:
            self.tmpl = template.Template.load(old_tmpl_key)

        current_tmpl_key = self.data['tmpl_key']
        self.data['tmpl_key'] = old_tmpl_key

        logger.info('[%s(%d)] Rolling back to template %s',
                    self.data['name'], self.key, old_tmpl_key)

        self._create_or_update(current_tmpl_key)

    def _create_or_update(self, current_tmpl_key=None):
        '''
        Update the stack.

        Create and Delete are special cases of Update, where the previous or
        new templates (respectively) are empty.
        '''
        self.data['current_traversal'] += 1
        self.store()

        definitions = self.tmpl.resources
        tmpl_deps = self.tmpl.dependencies()
        logger.debug('[%s(%d)] Dependencies: %s' % (self.data['name'],
                                                    self.key,
                                                    tmpl_deps.graph()))

        # Load all extant resources from the DB
        ext_rsrcs = set(resource.Resource.load_all_from_stack(self))

        def key(r):
            '''Return the GraphKey for a resource name.'''
            return resource.GraphKey(r, rsrcs[r].key)

        def best_existing_resource(rsrc_name):
            '''Return the best existing version of resource we want to keep.'''
            candidate = None

            for rsrc in ext_rsrcs:
                if rsrc.name != rsrc_name:
                    continue

                if rsrc.template_key == self.tmpl.key:
                    # BINGO! Rollback where the previous resource still exists
                    return rsrc
                elif rsrc.template_key == current_tmpl_key:
                    # Current resource is otherwise a good candidate
                    candidate = rsrc

            return candidate

        def get_resource(rsrc_name):
            '''
            Return the resource with the given name, creating it if necessary.

            This is the resource that will go into the update part of the
            graph. We also ensure its dependencies are updated to reflect the
            new template.
            '''
            rsrc = best_existing_resource(rsrc_name)
            if rsrc is None:
                rsrc = resource.Resource(rsrc_name, self,
                                         definitions[rsrc_name], self.tmpl.key)

            rqrs = set(key(r) for r in tmpl_deps.required_by(rsrc_name))
            rsrc.requirers = rsrc.requirers | rqrs

            return rsrc

        # Resources that will form the update part of the graph
        rsrcs = {}
        for rsrc_name in reversed(tmpl_deps):
            rsrc = get_resource(rsrc_name)
            rsrc.store()
            rsrcs[rsrc_name] = rsrc

        # Generate the entire graph
        dependencies = self._dependencies({resource.GraphKey(r.name, r.key): r
                                               for r in ext_rsrcs},
                                          tmpl_deps, rsrcs)

        list(dependencies)  # Check for circular deps

        # Start the traversal by sending notifications to the leaf nodes
        from . import processes
        for graph_key, forward in dependencies.leaves():
            processes.converger.check_resource(graph_key,
                                               self.current_traversal,
                                               {}, tuple(dependencies.edges()),
                                               forward)

    def mark_complete(self, traversal_id):
        '''
        Mark the update as complete.

        This currently occurs when all resources have been updated; there may
        still be resources being cleaned up, but the Stack should now be in
        service.
        '''
        if traversal_id != self.current_traversal:
            return

        logger.info('[%s(%d)] update traversal %d complete',
                    self.data['name'], self.key, traversal_id)

        prev_prev_key = self.data['prev_tmpl_key']
        self.data['prev_tmpl_key'] = self.data['tmpl_key']
        self.store()

        if (prev_prev_key is not None and
                prev_prev_key != self.data['tmpl_key']):
            template.templates.delete(prev_prev_key)

import logging

from .framework import datastore

from . import dependencies
from . import resource
from . import template


logger = logging.getLogger('stack')

stacks = datastore.Datastore('Stack',
                             'key', 'name', 'tmpl_key', 'deps')


class Stack(object):
    def __init__(self, name, tmpl, deps=tuple(), key=None):
        self.key = key
        self.tmpl = tmpl
        self.data = {
            'name': name,
            'tmpl_key': tmpl.key,
            'deps': deps,
        }

    def __str__(self):
        return '<Stack %r>' % self.key

    @classmethod
    def load(cls, key):
        s = stacks.read(key)
        return cls(s.name, template.Template.load(s.tmpl_key), s.deps,
                   key=s.key)

    @classmethod
    def load_by_name(cls, stack_name):
        candidates = list(stacks.find(name=stack_name))
        if not candidates:
            raise KeyError('Stack "%s" not found' % stack_name)
        assert len(candidates) == 1, 'Multiple stacks "%s" found' % stack_name
        return cls.load(candidates[0])

    def store(self):
        if self.key is None:
            self.key = stacks.create(**self.data)
        else:
            stacks.update(self.key, **self.data)

    def dependencies(self):
        return dependencies.Dependencies(self.data['deps'])

    def _calc_dependencies(self, tmpl_deps, resources):
        def make_graph_key(rsrc_name):
            return resources[rsrc_name].graph_key()

        deps = tmpl_deps.translate(make_graph_key)

        reverse_key = lambda gk: gk._replace(forward=False)

        for edge in self.data['deps']:
            src, targ = edge

            # Walk existing graph in reverse to clean up
            if targ is not None and targ.forward and src.forward:
                deps += (reverse_key(targ), reverse_key(src))

            # Keep existing clean up dependencies
            elif not src.forward and (targ is None or not targ.forward):
                deps += edge

            # Clean up only after handling the current resources
            for node in edge:
                if (node is not None and
                        node.forward and node.name in resources):
                    deps += (reverse_key(node), make_graph_key(node.name))

        return deps

    def create(self):
        self.store()

        logger.info('[%s(%d)] Created' % (self.data['name'], self.key))
        self._create_or_update()

    def update(self, tmpl):
        old_tmpl, self.tmpl = self.tmpl, tmpl
        self.data['tmpl_key'] = tmpl.key

        logger.info('[%s(%d)] Updating...' % (self.data['name'], self.key))
        self._create_or_update()

    def _create_or_update(self):
        current_graph = self.dependencies().graph()
        rsrcs = {r.name: r for r in resource.Resource.load_all_from_stack(self)
                           if r.graph_key() in current_graph}


        def store_resource(rsrc_name):
            rsrc = resource.Resource(rsrc_name, self, definitions[rsrc_name])
            rsrc.store()
            return rsrc

        definitions = self.tmpl.resources
        tmpl_deps = self.tmpl.dependencies()

        for rsrc_name in tmpl_deps:
            if rsrc_name not in rsrcs:
                rsrcs[rsrc_name] = store_resource(rsrc_name)

        deps = self._calc_dependencies(tmpl_deps, rsrcs)
        list(deps) # Check for circular dependencies
        self.data['deps'] = tuple(deps.graph().edges())

        self.store()

        from . import processes
        for graph_key in deps.leaves():
            if graph_key.forward:
                processes.converger.check_resource(graph_key.key,
                                                   self.tmpl.key)

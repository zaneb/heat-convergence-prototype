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

    def _calc_dependencies(self, tmpl_deps, resources, current_res_names,
                           existing_res_keys):

        def make_graph_key(rsrc_name):
            return resources[rsrc_name].graph_key()

        deps = tmpl_deps.translate(make_graph_key)

        reverse_key = lambda gk: gk._replace(forward=False)

        for edge in self.data['deps']:
            src, targ = edge

            # Walk existing graph in reverse to clean up
            if targ is not None and targ.forward and src.forward:
                deps += (reverse_key(targ), reverse_key(src))

            # Keep existing clean up dependencies if the resources still exist
            elif (not src.forward and (targ is None or not targ.forward) and
                    existing_res_keys.issuperset(edge)):
                deps += edge

            # Clean up only after handling the current resources
            for node in edge:
                if (node is not None and
                        node.forward and node.name in current_res_names):
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

    def delete(self):
        self.tmpl = template.Template()
        self.data['tmpl_key'] = None

        logger.info('[%s(%d)] Deleting...' % (self.data['name'], self.key))
        self._create_or_update()

    def _create_or_update(self):
        current_graph = self.dependencies().graph()
        ext_rsrcs = {r.graph_key(): r
                         for r in resource.Resource.load_all_from_stack(self)}
        rsrcs = {r.name: r for gk, r in ext_rsrcs.items()
                           if gk in current_graph}


        def store_resource(rsrc_name):
            rsrc = resource.Resource(rsrc_name, self, definitions[rsrc_name])
            rsrc.store()
            return rsrc

        definitions = self.tmpl.resources
        tmpl_deps = self.tmpl.dependencies()
        current_res_names = list(tmpl_deps)

        for rsrc_name in current_res_names:
            if rsrc_name not in rsrcs:
                rsrcs[rsrc_name] = store_resource(rsrc_name)

        deps = self._calc_dependencies(tmpl_deps, rsrcs,
                                       set(current_res_names),
                                       set(ext_rsrcs.keys()))
        list(deps) # Check for circular dependencies
        self.data['deps'] = tuple(deps.graph().edges())

        self.store()

        from . import processes
        for graph_key in deps.leaves():
            processes.converger.check_resource(graph_key.key,
                                               self.tmpl.key,
                                               graph_key.forward)

    def create_replacement(self, rsrc_name, rsrc_defn, prev_rsrc_key):
        rsrc = resource.Resource(rsrc_name, self, rsrc_defn)
        rsrc.store()

        def rewrite_deps(edges):
            for src, targ in edges:
                if src.key == prev_rsrc_key and src.forward:
                    yield rsrc.graph_key(), targ

                if targ.key == prev_rsrc_key and targ.forward:
                    # This is wrong, because we sometimes need to update the
                    # src to require the new targ. Sometimes we don't,
                    # however - when the src itself will be replaced. But we
                    # won't make a decision on that until The Future.
                    yield src, targ
                else:
                    yield src, targ

        # This part is quite problematic, as it requires us to somehow lock
        # the stack so we can rewrite the dependency graph at a time when
        # other resource replacements and/or new template updates may be
        # trying to do the same.
        self.data['deps'] = tuple(rewrite_deps(self.data['deps']))
        self.store()

        return rsrc

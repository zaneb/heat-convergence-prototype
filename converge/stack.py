import logging

from .framework import datastore

from . import dependencies
from . import resource
from . import template


logger = logging.getLogger('stack')

stacks = datastore.Datastore('Stack',
                             'key', 'name', 'tmpl_key', 'prev_tmpl_key')


class Stack(object):
    def __init__(self, name, tmpl, prev_tmpl_key=None, key=None):
        self.key = key
        self.tmpl = tmpl
        self.data = {
            'name': name,
            'tmpl_key': tmpl.key,
            'prev_tmpl_key': prev_tmpl_key,
        }

    def __str__(self):
        return '<Stack %r>' % self.key

    @classmethod
    def load(cls, key):
        s = stacks.read(key)
        return cls(s.name, template.Template.load(s.tmpl_key),
                   key=s.key)

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
        def make_graph_key(res_name):
            return (resource.GraphKey(res_name,
                                      current_resources[res_name].key),
                    True)

        deps = current_template_deps.translate(make_graph_key)

        for key, rsrc in existing_resources.items():
            deps += (key, False), None

            # Note: reversed edges as this is the cleanup part of the graph
            for requirer in rsrc.requirers:
                if requirer in existing_resources:
                    deps += (key, False), (requirer, False)
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

    def _create_or_update(self, current_tmpl_key=None):
        self.store()

        definitions = self.tmpl.resources
        tmpl_deps = self.tmpl.dependencies()
        logger.debug('[%s(%d)] Dependencies: %s' % (self.data['name'],
                                                    self.key,
                                                    tmpl_deps.graph()))

        def is_fresh(rsrc):
            return rsrc.template_key == current_tmpl_key

        ext_rsrcs = set(resource.Resource.load_all_from_stack(self))
        rsrcs = {r.name: r for r in ext_rsrcs if is_fresh(r) and
                                                 r.name in definitions}

        def key(r):
            return resource.GraphKey(r, rsrcs[r].key)

        def store_resource(name):
            requirers = (key(r) for r in tmpl_deps.required_by(name))
            rsrc = resource.Resource(rsrc_name, self, definitions[name],
                                     self.tmpl.key, set(requirers))
            rsrc.store()
            return rsrc

        for rsrc_name in reversed(tmpl_deps):
            if rsrc_name not in rsrcs:
                rsrcs[rsrc_name] = store_resource(rsrc_name)
            else:
                rsrc = rsrcs[rsrc_name]
                rsrc.requirers |= set(key(r) for r in
                        tmpl_deps.required_by(rsrc.name))
                rsrc.store()

        dependencies = self._dependencies({resource.GraphKey(r.name, r.key): r
                                               for r in ext_rsrcs},
                                          tmpl_deps, rsrcs)

        from . import processes
        for graph_key, forward in dependencies.leaves():
            processes.converger.check_resource(graph_key, self.tmpl.key,
                                               {}, dependencies, forward)

    def mark_complete(self, template_key):
        if template_key != self.tmpl.key:
            return

        logger.info('[%s(%d)] update to template %d complete',
                    self.data['name'], self.key, template_key)

        prev_prev_key = self.data['prev_tmpl_key']
        self.data['prev_tmpl_key'] = template_key
        self.store()

        if prev_prev_key is not None and prev_prev_key != template_key:
            template.templates.delete(prev_prev_key)

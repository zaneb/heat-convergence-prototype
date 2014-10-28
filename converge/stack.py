import logging

from .framework import datastore

from . import resource
from . import template


logger = logging.getLogger('stack')

stacks = datastore.Datastore('Stack',
                             'key', 'name', 'tmpl_key')


class Stack(object):
    def __init__(self, name, tmpl, key=None):
        self.key = key
        self.tmpl = tmpl
        self.data = {
            'name': name,
            'tmpl_key': tmpl.key,
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
            raise KeyError('Stack "%s" not found' % stack_name)
        assert len(candidates) == 1, 'Multiple stacks "%s" found' % stack_name
        return cls.load(candidates[0])

    def store(self):
        if self.key is None:
            self.key = stacks.create(**self.data)
        else:
            stacks.update(self.key, **self.data)

    def create(self):
        self.store()

        logger.info('[%s(%d)] Created' % (self.data['name'], self.key))

        definitions = self.tmpl.resources
        deps = self.tmpl.dependencies()
        logger.debug('[%s(%d)] Dependencies: %s' % (self.data['name'],
                                                    self.key, deps.graph()))

        resources = {}
        for rsrc_name in reversed(deps):
            requirers = [resources[r].key for r in deps.required_by(rsrc_name)]
            rsrc = resource.Resource(rsrc_name, self, definitions[rsrc_name],
                                     self.tmpl.key, set(requirers))
            rsrc.store()
            resources[rsrc_name] = rsrc

        from . import processes
        for rsrc_name in deps.leaves():
            processes.converger.check_resource(resources[rsrc_name].key,
                                               self.tmpl.key)

    def update(self, tmpl):
        old_tmpl, self.tmpl = self.tmpl, tmpl
        self.data['tmpl_key'] = tmpl.key
        self.store()

        logger.info('[%s(%d)] Updating...' % (self.data['name'], self.key))

        definitions = self.tmpl.resources
        tmpl_deps = self.tmpl.dependencies()
        logger.debug('[%s(%d)] Dependencies: %s' % (self.data['name'],
                                                    self.key,
                                                    tmpl_deps.graph()))

        rsrcs = {r.name: r for r in resource.Resource.load_all_from_stack(self)
                           if r.template_key == old_tmpl.key}

        def store_resource(name):
            requirers = [rsrcs[r].key for r in tmpl_deps.required_by(name)]
            rsrc = resource.Resource(rsrc_name, self, definitions[name],
                                     self.tmpl.key, set(requirers))
            rsrc.store()
            return rsrc

        for rsrc_name in reversed(tmpl_deps):
            if rsrc_name not in rsrcs:
                rsrcs[rsrc_name] = store_resource(rsrc_name)
            else:
                rsrc = rsrcs[rsrc_name]
                rsrc.requirers |= set(rsrcs[r].key for r in
                        tmpl_deps.required_by(rsrc.name))
                rsrc.store()

        from . import processes
        for rsrc_name in tmpl_deps.leaves():
            processes.converger.check_resource(rsrcs[rsrc_name].key,
                                               self.tmpl.key)

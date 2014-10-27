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
        self._create_or_update()

    def update(self, tmpl):
        old_tmpl, self.tmpl = self.tmpl, tmpl
        self.data['tmpl_key'] = tmpl.key

        logger.info('[%s(%d)] Updating...' % (self.data['name'], self.key))
        self._create_or_update(old_tmpl.key)

    def _create_or_update(self, current_tmpl_key=None):
        self.store()

        definitions = self.tmpl.resources
        tmpl_deps = self.tmpl.dependencies()
        logger.debug('[%s(%d)] Dependencies: %s' % (self.data['name'],
                                                    self.key,
                                                    tmpl_deps.graph()))

        rsrcs = {r.name: r for r in resource.Resource.load_all_from_stack(self)
                           if r.template_key == current_tmpl_key}

        def key(r):
            return resource.GraphKey(r, rsrcs[r].key)

        def store_resource(name):
            requirers = [key(r) for r in tmpl_deps.required_by(name)]
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

        from . import processes
        for rsrc_name in tmpl_deps.leaves():
            processes.converger.check_resource(key(rsrc_name), self.tmpl.key)

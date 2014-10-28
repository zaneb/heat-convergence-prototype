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

    def create(self):
        self.store()

        logger.info('[%s(%d)] Created' % (self.data['name'], self.key))

        definitions = self.tmpl.resources
        deps = self.tmpl.dependencies()
        logger.debug('[%s(%d)] Dependencies: %s' % (self.data['name'],
                                                    self.key, deps.graph()))

        def store_resource(rsrc_name):
            rsrc = resource.Resource(rsrc_name, self, definitions[rsrc_name])
            rsrc.store()
            return rsrc

        resources = {name: store_resource(name) for name in deps}

        def get_res_id(rsrc_name):
            return resources[rsrc_name].key if rsrc_name is not None else None

        edges = tuple(tuple(map(get_res_id, e)) for e in deps.graph().edges())
        self.data['deps'] += edges
        self.store()

        from . import processes
        for rsrc_name in deps.leaves():
            processes.converger.check_resource(resources[rsrc_name].key,
                                               self.tmpl.key)

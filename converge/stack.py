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

    def store(self):
        if self.key is None:
            self.key = stacks.create(**self.data)
        else:
            stacks.update(self.key, **self.data)

    def create(self):
        self.store()

        logger.info('[%s(%d)] Created' % (self.data['name'], self.key))

        resources = {name: resource.Resource(name, self, defn)
                         for name, defn in self.tmpl.resources.items()}

        for rsrc in resources.values():
            rsrc.store()

        from . import processes
        for rsrc in resources.values():
            processes.converger.check_resource(rsrc.key)

import logging

from .framework import datastore

from . import resource


logger = logging.getLogger('stack')

stacks = datastore.Datastore('Stack',
                             'key', 'name')


class Stack(object):
    def __init__(self, name, key=None):
        self.key = key
        self.data = {
            'name': name,
        }

    def __str__(self):
        return '<Stack %r>' % self.key

    @classmethod
    def load(cls, key):
        return cls(**stacks.read(key)._asdict())

    def store(self):
        if self.key is None:
            self.key = stacks.create(**self.data)
        else:
            stacks.update(self.key, **self.data)

    def create(self):
        self.store()

        logger.info('[%s(%d)] Created' % (self.data['name'], self.key))

        res_names = ('A', 'B', 'C')
        resources = {name: resource.Resource(name, self) for name in res_names}

        for rsrc in resources.values():
            rsrc.store()

        from . import processes
        for rsrc in resources.values():
            processes.converger.check_resource(rsrc.key)

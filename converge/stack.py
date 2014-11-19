import logging

from .framework import datastore

logger = logging.getLogger('stack')

stacks = datastore.Datastore('Stack',
                             'key', 'name', 'tmpl_key')

stack_resources = datastore.Datastore(
    'StackResources',
    'key',
    'name',
    'properties',
    'depends_on',
    'stack',
    'state',
)


class Stack(object):
    def __init__(self, name, tmpl, deps=tuple(), key=None):
        self.key = key
        self.tmpl = tmpl
        self.data = {
            'name': name,
            'tmpl_key': tmpl.key,
        }

    def __str__(self):
        return '<Stack %r>' % self.key

    @staticmethod
    def load_by_name(stack_name):
        return stacks.find(name=stack_name)

    def create(self):
        self.key = stacks.create(**self.data)
        for res_name, res_def in self.tmpl.resources.iteritems():
            stack_resources.create(**{
                'name': res_name,
                'stack': self.key,
                'depends_on': res_def.depends_on,
                'properties': res_def.properties,
                'state': 'COMPLETE',
            })

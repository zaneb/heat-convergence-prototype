import logging

from .framework import datastore
from . import template

logger = logging.getLogger('stack')

stacks = datastore.Datastore('Stack',
                             'key', 'name', 'tmpl_key', 'version')

stack_resources = datastore.Datastore(
    'StackResources',
    'key',
    'name',
    'properties',
    'depends_on',
    'stack',
    'state',
)


def get_stack_resource_by_name(name):
    sorted_stacks = [
        s for s in sorted(
            stacks._store.itervalues(), key=lambda s: s.version * -1
        )
    ]
    for stack_key in sorted_stacks:
        stack = Stack.load_by_key(stack_key.key)
        for resource in stack.get_resources():
            if resource.name == name:
                return resource


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

    @classmethod
    def load_by_name(cls, stack_name):
        stack_ds = sorted(
            filter(
                lambda stack: stack.name == stack_name,
                list(stacks._store.values())
            ),
            key=lambda stack: stack.version * -1
        )[0]
        tmpl = template.Template.load(stack_ds.tmpl_key)
        return cls(name=stack_ds.name, tmpl=tmpl, key=stack_ds.key)

    @classmethod
    def load_by_key(cls, key):
        stack_ds = stacks.read(key)
        tmpl = template.Template.load(stack_ds.tmpl_key)
        return cls(name=stack_ds.name, tmpl=tmpl, key=stack_ds.key)

    def create(self, version=1):
        """
        All actions like create changes "goal stacks", not reality. This way
        it will be very small operation (in comparason to actually creating
        stacks), and it can be transaction.
        """
        self.key = stacks.create(version=version, **self.data)
        for res_name, res_def in self.tmpl.resources.iteritems():
            stack_resources.create(**{
                'name': res_name,
                'stack': self.key,
                'depends_on': res_def.depends_on,
                'properties': res_def.properties,
                'state': 'COMPLETE',
            })

    def update(self, tmpl):
        self.data['tmpl_key'] = tmpl.key
        self.tmpl = tmpl
        old_version = stacks.read(self.key).version
        self.create(version=old_version + 1)

    def get_resources(self):
        resources = stack_resources.find(stack=self.key)
        return map(lambda rkey: stack_resources.read(rkey), resources)

    def delete(self):
        empty_template = template.Template({})
        self.update(empty_template)

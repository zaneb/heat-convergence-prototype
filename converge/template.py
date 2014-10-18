import logging

from .framework import datastore

from . import resource


logger = logging.getLogger('tmpl ')

templates = datastore.Datastore('Template',
                                'key',
                                'resources')


class GetRes(object):
    def __init__(self, target_name):
        self.target_name = target_name

    def __repr__(self):
        return 'GetRes(%r)' % self.target_name


class GetAtt(GetRes):
    def __init__(self, target_name, attr):
        super(GetAtt, self).__init__(target_name)
        self.attr = attr

    def __repr__(self):
        return 'GetAtt(%r, %r)' % (self.target_name, self.attr)


class RsrcDef(object):
    def __init__(self, properties, depends_on):
        self.properties = properties
        self.depends_on = depends_on

    def __repr__(self):
        return 'RsrcDef(%r, %r)' % (self.properties, self.depends_on)

    def dependency_names(self):
        for dep in self.depends_on:
            yield dep

        for prop in self.properties.values():
            if isinstance(prop, GetRes):
                yield prop.target_name


class Template(object):
    def __init__(self, resources={}, key=None):
        self.key = key
        self.resources = resources

    def __repr__(self):
        return 'Template(%r)' % self.resources

    @classmethod
    def load(cls, key):
        return cls(**templates.read(key)._asdict())

    def store(self):
        if self.key is None:
            self.key = templates.create(resources=self.resources)
        else:
            templates.update(self.key)

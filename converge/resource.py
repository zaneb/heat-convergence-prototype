from .framework import datastore
from .stack import stack_resources


resources = datastore.Datastore(
    'Resource',
    'key',
    'phys_id',
    'name',
    'properties',
    'state',
)


class Resource(object):
    def __init__(self, key):
        self.data = resources.read(key)

    @staticmethod
    def update_or_create(key=None, **data):
        state = 'COMPLETE'
        if not Resource.check_create_readiness(data['name']):
            state = 'ERROR'
        resource = {
            'name': data['name'],
            'properties': data['properties'],
            'state': state,
            'phys_id': '{}_phys_id'.format(data['name'])
        }
        if key is not None:
            resource.update({'key': key})
            resources.update(**resource)
        else:
            resources.create(**resource)

    def delete(self):
        if not Resource.check_delete_readiness(self.name):
            pass

    @staticmethod
    def check_create_readiness(res_name):
        equivalent = stack_resources.read(
            stack_resources.find(name=res_name).next()
        )
        for dependency_name in equivalent.depends_on:
            try:
                dependency = stack_resources.read(
                    resources.find(name=dependency_name).next()
                )
            except StopIteration:
                dependency = None
            if not dependency or dependency.state != 'COMPLETE':
                return False
        return True

    @staticmethod
    def check_delete_readiness(res_name):
        for resource_key in stack_resources.keys:
            res = stack_resources.read(resource_key)
            if res_name in res.depends_on:
                return False
        return True

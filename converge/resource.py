from .framework import datastore
from .stack import stack_resources, get_stack_resource_by_name
from .template import GetAtt, GetRes


resources = datastore.Datastore(
    'Resource',
    'key',
    'phys_id',
    'name',
    'properties',
    'state',
)


class Resource(object):
    """
    This class simulates "real resources", therefore it has no notion of
    dependency here. Statuses and dependency checks in create/delete/update are
    for validation purposes
    """
    def __init__(self, key):
        self.data = resources.read(key)

    @staticmethod
    def update_or_create(key=None, **data):
        state = 'COMPLETE'
        if not Resource.check_create_readiness(data['name']):
            state = 'ERROR'
        for prop, prop_value in data['properties'].iteritems():
            if type(prop_value) == GetRes:
                source = resources.read(
                    resources.find(
                        name=prop_value.target_name,
                    ).next()
                )
                data['properties'][prop] = source.phys_id
            if type(prop_value) == GetAtt:
                source = resources.read(
                    resources.find(
                        name=prop_value.target_name,
                    ).next()
                )
                data['properties'][prop] = source.properties[prop_value.attr]
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
        """
        This is logic we might potentially have to implement in resource api.
        Resource objects should have methods to determine if all dependencies
        for actions have been met
        """
        equivalent = get_stack_resource_by_name(res_name)
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

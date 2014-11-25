from .framework import datastore

import copy
import uuid


class RealityStore(object):
    def __init__(self):
        self.store = datastore.Datastore('PhysicalResource', 'uuid',
                                         'logical_name', 'properties')

    def create_resource(self, logical_name, properties):
        key = uuid.uuid4()
        self.store.create_with_key(key, logical_name=logical_name,
                                   properties=properties)
        return key

    def update_resource(self, uuid, properties):
        self.store.update(uuid, properties=properties)

    def delete_resource(self, uuid):
        self.store.delete(uuid)

    def resources_by_logical_name(self, logical_name):
        keys = self.store.find(logical_name=logical_name)
        return {key: self.store.read(key) for key in keys}

    def all_resources(self):
        return copy.deepcopy(self.store._store)


reality = RealityStore()

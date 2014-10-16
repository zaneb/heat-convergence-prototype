from .framework import process

from . import resource


class Converger(process.MessageProcessor):
    def __init__(self):
        super(Converger, self).__init__('converger')

    @process.asynchronous
    def check_resource(self, resource_key):
        rsrc = resource.Resource.load(resource_key)
        if rsrc.physical_resource_id is None:
            rsrc.create()


from .framework import process
from . import resource
from . import stack


class Converger(process.MessageProcessor):
    def __init__(self):
        super(Converger, self).__init__('converger')

    def get_reality(self):
        reality = []
        for resource_key in resource.resources.keys:
            res = resource.resources.read(resource_key)
            reality.append({
                'name': res.name,
                'state': res.state,
                'properties': res.properties,
            })
        return reality

    def get_goal(self):
        goal = []
        for resource_key in stack.stack_resources.keys:
            res = stack.stack_resources.read(resource_key)
            goal.append({
                'name': res.name,
                'state': 'COMPLETE',
                'properties': res.properties,
            })
        return goal

    def get_diff(self, reality, goal):
        actions = {}
        # resources to create
        for resource in goal:
            if resource['name'] not in [r['name'] for r in reality]:
                actions[resource['name']] = 'create'
        # resources to delete
        for resource in reality:
            if resource['name'] not in [r['name'] for r in goal]:
                actions[resource['name']] = 'delete'
        return actions

    def get_possible_actions(self, actions):
        possible_actions = []
        for res_name, action in actions.iteritems():
            create_ready = resource.Resource.check_create_readiness(res_name)
            if action == 'create' and create_ready:
                possible_actions.append(res_name)
            delete_ready = resource.Resource.check_delete_readiness(res_name)
            if action == 'delete' and delete_ready:
                possible_actions.append(res_name)
        return possible_actions

    def worker(self, action, res_name):
        if action == 'create':
            res = stack.stack_resources.read(
                stack.stack_resources.find(name=res_name).next()
            )
            resource.Resource.update_or_create(
                name=res.name,
                properties=res.properties,
            )

    def converge(self, stack_name):
        self.stack_name = stack_name
        reality = self.get_reality()
        goal = self.get_goal()
        all_actions = self.get_diff(reality, goal)
        possible_actions = self.get_possible_actions(all_actions)
        for res_name in possible_actions:
            self.worker(all_actions[res_name], res_name)

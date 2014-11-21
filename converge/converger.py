
from .framework import process
from . import resource
from . import stack


class Converger(process.MessageProcessor):
    def __init__(self):
        super(Converger, self).__init__('converger')

    def get_reality(self):
        """
        This checks real state of resources and cast it to comparable
        datastructure
        """
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
        """
        This parses stack from template and casts it to comparable
        datastructure
        """
        goal = []
        for res in self.stack.get_resources():
            goal.append({
                'name': res.name,
                'state': 'COMPLETE',
                'properties': res.properties,
            })
        return goal

    def get_diff(self, reality, goal):
        """
        This method compares real env state (real resources like nova instance)
        to state described in graph. In fact its most crucial part of whole
        algorithm. One tricky part I see would be converting graph differences
        to actions fixing them. While create/delete are fairly easy, update is
        a bit trickier, but still managable, autohealing actions will require
        policies which will take diagnostics and return best autoheal action.
        But that is future:)
        """
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
        """
        This method filters list of all actions which brings us closer to goal
        stack, and returns only these, for which every dependency has been met.
        """
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
        """
        Ideally this will be separate worker process. It will consume single
        task from queue and perform it.
        """
        if action == 'create':
            res = stack.stack_resources.read(
                stack.stack_resources.find(name=res_name).next()
            )
            resource.Resource.update_or_create(
                name=res.name,
                properties=res.properties,
            )

    def converge(self, stack_name):
        """
        Main convergence process (this one can be embedded to heat-engine).
        Its main purpose is to return tasks which are possible *right now*
        and which will bring us a little closer to goal stack described in
        template.
        """
        self.stack = stack.Stack.load_by_name(stack_name)
        reality = self.get_reality()
        goal = self.get_goal()
        all_actions = self.get_diff(reality, goal)
        possible_actions = self.get_possible_actions(all_actions)
        for res_name in possible_actions:
            # this part, instead of calling worker here, will add task to task
            # queue. Worker process will consume it asynchronously.
            self.worker(all_actions[res_name], res_name)

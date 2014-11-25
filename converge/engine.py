from .framework import process
from . import stack
from . import converger


class Engine(process.MessageProcessor):
    def __init__(self):
        super(Engine, self).__init__('engine')

    @process.asynchronous
    def create_stack(self, stack_name, tmpl):
        tmpl.store()

        new_stack = stack.Stack(stack_name, tmpl)
        new_stack.create()
        self.start_converge(stack_name)

    @process.asynchronous
    def update_stack(self, stack_name, tmpl):
        tmpl.store()
        existing_stack = stack.Stack.load_by_name(stack_name)
        existing_stack.update(tmpl)
        self.start_converge(stack_name)

    @process.asynchronous
    def delete_stack(self, stack_name):
        existing_stack = stack.Stack.load_by_name(stack_name)
        existing_stack.delete()
        self.start_converge(stack_name)

    def start_converge(self, stack_name):
        from . import processes
        processes.converger.converge(stack_name)

from .framework import process
from . import stack
from . import template


class Engine(process.MessageProcessor):
    def __init__(self):
        super(Engine, self).__init__('engine')

    @process.asynchronous
    def create_stack(self, stack_name, tmpl):
        tmpl.store()

        new_stack = stack.Stack(stack_name, tmpl)
        new_stack.create()

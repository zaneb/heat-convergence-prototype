from .framework import process
from . import stack


class Engine(process.MessageProcessor):
    def __init__(self):
        super(Engine, self).__init__('engine')

    @process.asynchronous
    def create_stack(self, stack_name):
        new_stack = stack.Stack(stack_name)
        new_stack.create()

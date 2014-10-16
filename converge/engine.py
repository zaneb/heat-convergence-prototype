from .framework import process
from . import stacks


class Engine(process.MessageProcessor):
    def __init__(self):
        super(Engine, self).__init__('engine')

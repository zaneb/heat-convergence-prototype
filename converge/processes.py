from .framework.event_loop import EventLoop

from .engine import Engine
from .converger import Converger


engine = None
converger = None
event_loop = None


class Processes(object):
    def __init__(self):
        global engine
        global converger
        global event_loop

        engine = Engine()
        converger = Converger()

        event_loop = EventLoop(engine, converger, converger.worker)

        self.engine = engine
        self.converger = converger
        self.event_loop = event_loop


Processes()

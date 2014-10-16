from .framework.event_loop import EventLoop

from .engine import Engine
from .converger import Converger


engine = Engine()
converger = Converger()

event_loop = EventLoop(engine, converger)

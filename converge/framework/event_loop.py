import logging


logger = logging.getLogger('event')
logger.setLevel(logging.INFO)


class EventLoop(object):
    def __init__(self, *processors):
        self.processors = processors

    def __call__(self):
        while any(processor() for processor in self.processors):
            continue

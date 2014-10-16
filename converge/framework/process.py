import collections
import functools
import inspect
import logging

from . import message_queue


logger = logging.getLogger('event')


def asynchronous(function):
    '''Decorator for MessageProcessor methods to make them asynchronous.

    To use, simply call the method as usual. Instead of being executed
    immediately, it will be placed on the queue for the MessageProcessor and
    run on a future iteration of the event loop.
    '''
    arg_names = inspect.getargspec(function).args
    MessageData = collections.namedtuple(function.func_name, arg_names[1:])

    @functools.wraps(function)
    def call_or_send(processor, *args, **kwargs):
        if len(args) == 1 and not kwargs and isinstance(args[0], MessageData):
            return function(processor, **args[0]._asdict())
        else:
            data = inspect.getcallargs(function, processor, *args, **kwargs)
            data.pop(arg_names[0])  # lose self
            return processor.queue.send(function.func_name,
                                        MessageData(**data))

    call_or_send.MessageData = MessageData
    return call_or_send


class MessageProcessor(object):
    def __init__(self, name):
        self.name = name
        self.queue = message_queue.MessageQueue(name)

    def __call__(self):
        message = self.queue.get()
        if message is None:
            logger.debug('[%s] No messages' % self.name)
            return False

        try:
            method = getattr(self, message.name)
        except AttributeError:
            logger.error('[%s] Bad message name "%s"' % (self.name,
                                                         message.name))
            raise
        else:
            logger.info('[%s] %r' % (self.name, message.data))

        method(message.data)
        return True

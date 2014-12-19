import collections
import functools
import inspect
import logging
import sys

from . import debug
from . import message_queue


logger = logging.getLogger('event')

_breakpoint_candidates = []


def _set_breakpoint(debugger, function):
    if function.__module__ != __name__:
        code = function.__code__
        fn = code.co_filename
        line = code.co_firstlineno

        if not debugger.get_breaks(fn, line):
            debugger.set_break(fn, line, funcname=code.co_name)


def asynchronous(function):
    '''Decorator for MessageProcessor methods to make them asynchronous.

    To use, simply call the method as usual. Instead of being executed
    immediately, it will be placed on the queue for the MessageProcessor and
    run on a future iteration of the event loop.
    '''
    arg_names = inspect.getargspec(function).args
    MessageData = collections.namedtuple(function.__name__, arg_names[1:])

    if function not in _breakpoint_candidates:
        _breakpoint_candidates.append(function)

    @functools.wraps(function)
    def call_or_send(processor, *args, **kwargs):
        if len(args) == 1 and not kwargs and isinstance(args[0], MessageData):
            try:
                return function(processor, **args[0]._asdict())
            except debug.Quit:
                raise
            except Exception as exc:
                logger.exception('[%s] Exception in "%s": %s',
                                 processor.name, function.__name__, exc)
                raise
        else:
            data = inspect.getcallargs(function, processor, *args, **kwargs)
            data.pop(arg_names[0])  # lose self
            return processor.queue.send(function.__name__,
                                        MessageData(**data))

    call_or_send.MessageData = MessageData
    return call_or_send


class MessageProcessor(object):

    def __init__(self, name):
        self.name = name
        self.queue = message_queue.MessageQueue(name)
        self.debugger = None

    def set_debugger(self, debugger):
        self.debugger = debugger
        for bp_func in _breakpoint_candidates:
            _set_breakpoint(debugger, bp_func)

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

    @asynchronous
    def noop(self, count=1):
        '''
        Insert <count> No-op operations in the message queue.
        '''
        assert isinstance(count, int)
        if count > 1:
            self.queue.send_priority('noop',
                                     self.noop.MessageData(count - 1))

    @asynchronous
    def _execute(self, func):
        '''
        Insert a function call in the message queue.

        The function takes no arguments, so use functools.partial to curry the
        arguments before passing it here.
        '''
        func()

    def call(self, func, *args, **kwargs):
        '''
        Insert a function call in the message queue.
        '''
        self._execute(functools.partial(func, *args, **kwargs))


__all__ = ['MessageProcessor', 'asynchronous']

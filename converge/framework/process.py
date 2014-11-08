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

    def testproxy(self, testcase=None):
        return TestProxy(self, testcase)

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
    def execute_func(self, func):
        '''
        Insert a function call in the message queue.

        The function takes no arguments, so use functools.partial to curry the
        arguments before passing it here.
        '''
        func()


class TestProxy(object):
    def __init__(self, msg_processor, testcase=None):
        self.msg_processor = msg_processor
        self.testcase = testcase
        self.logger = logging.getLogger('testproxy')

    @staticmethod
    def __format_args(args, kwargs):
        for a in args:
            yield repr(a)
        for kw, a in kwargs.items():
            yield '%s=%s' % (kw, repr(a))

    def _log_assertion(self, func_name, *args, **kwargs):
        self.logger.warning('Ignoring %s(%s)',
                            func_name,
                            ', '.join(TestProxy.__format_args(args, kwargs)))

    def __getattr__(self, name):
        if name.startswith('assert'):
            def handler(*args, **kwargs):
                if self.testcase is not None:
                    handler = getattr(self.testcase, name)
                    wrappee = handler
                else:
                    handler = functools.partial(self._log_assertion, name)
                    wrappee = self._log_assertion

                @functools.wraps(wrappee)
                def do_assert():
                    try:
                        handler(*args, **kwargs)
                    except AssertionError as exc:
                        self.logger.exception('AssertionError: %s', exc)
                        raise

                self.msg_processor.execute_func(do_assert)

            return handler
        else:
            raise AttributeError(name)

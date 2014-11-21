import functools
import logging


logger = logging.getLogger('test')


def _format_args(args, kwargs):
    for a in args:
        yield repr(a)
    for kw, a in kwargs.items():
        yield '%s=%s' % (kw, repr(a))


def _log_assertion(func_name, *args, **kwargs):
    logger.warning('Ignoring %s(%s)',
                   func_name, ', '.join(_format_args(args, kwargs)))


class DummyTestCase(object):
    def __getattr__(self, name):
        if name.startswith('assert'):
            return functools.partial(_log_assertion, name)
        else:
            raise AttributeError(name)

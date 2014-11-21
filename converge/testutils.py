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


def verify(test, reality, template):
    for name, defn in template.resources.items():
        phys_rsrcs = reality.resources_by_logical_name(name)
        rsrc_count = len(phys_rsrcs)
        test.assertEqual(1, rsrc_count,
                         'Found %d copies of resource "%s"' % (rsrc_count,
                                                               name))

        phys_rsrc = phys_rsrcs.values()[0]
        test.assertEqual(defn.properties, phys_rsrc.properties)

    test.assertEqual(len(template.resources), len(reality.all_resources()))

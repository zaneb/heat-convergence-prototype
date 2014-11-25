import functools
import logging

from . import template


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


def verify(test, reality, tmpl):
    for name in tmpl.resources:
        rsrc_count = len(reality.resources_by_logical_name(name))
        test.assertEqual(1, rsrc_count,
                         'Found %d copies of resource "%s"' % (rsrc_count,
                                                               name))

    all_rsrcs = reality.all_resources()

    for name, defn in tmpl.resources.items():
        phys_rsrc = list(reality.resources_by_logical_name(name).values())[0]

        for prop_name, prop_def in defn.properties.items():
            real_value = phys_rsrc.properties[prop_name]

            if isinstance(prop_def, template.GetAtt):
                targs = reality.resources_by_logical_name(prop_def.target_name)
                att_value = list(targs.values())[0].properties[prop_def.attr]
                test.assertEqual(att_value, real_value)

            elif isinstance(prop_def, template.GetRes):
                targs = reality.resources_by_logical_name(prop_def.target_name)
                test.assertEqual(list(targs)[0], real_value['phys_id'])

            else:
                test.assertEqual(prop_def, real_value)

        test.assertEqual(len(defn.properties), len(phys_rsrc.properties))

    test.assertEqual(len(tmpl.resources), len(all_rsrcs))

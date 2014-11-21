'''
An OpenStack Heat convergence algorithm simulator.
'''

import logging


def setup_log(logger):
    log_handler = logging.StreamHandler()
    log_handler.setLevel(logging.DEBUG)

    log_formatter = logging.Formatter('%(levelname) -8s %(name)s: %(message)s')
    log_handler.setFormatter(log_formatter)

    logger.addHandler(log_handler)
    logger.setLevel(logging.DEBUG)


def scenario_globals(procs, testcase=None):
    from . import template
    from . import reality

    return {
        'test': procs.engine.testproxy(testcase),
        'reality': reality.reality,

        'Template': template.Template,
        'RsrcDef': template.RsrcDef,
        'GetRes': template.GetRes,
        'GetAtt': template.GetAtt,

        'engine': procs.engine,
        'converger': procs.converger,
    }


def cli_options():
    import sys
    from optparse import OptionParser

    parser = OptionParser(prog='%s -m %s' % (sys.executable, __name__),
                          usage='usage: %prog [options] SCENARIOS',
                          description=__doc__)
    parser.add_option('-d', '--scenario-directory', dest='directory',
                      action='store', default='scenarios', metavar='DIR',
                      help='Directory to read scenarios from')

    return parser.parse_args()


def main(config=None):
    if config is None:
        config = cli_options()
    options, scenario_names = config

    if not logging.root.handlers:
        setup_log(logging.root)

    logger = logging.getLogger(__name__)

    from . import processes
    from .framework import datastore
    from .framework import scenario

    def include_scenario(name):
        return not scenario_names or name in scenario_names

    for runner in scenario.Scenario.load_all(options.directory):
        if not include_scenario(runner.name):
            continue

        try:
            procs = processes.Processes()
            runner(procs.event_loop, **scenario_globals(procs))
        except Exception as exc:
            logger.exception('Exception in scenario "%s"', runner.name)
        finally:
            datastore.Datastore.clear_all()


__all__ = ['setup_log', 'scenario_globals', 'cli_options', 'main']

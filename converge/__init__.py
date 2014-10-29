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

    return {
        'test': procs.engine.testproxy(testcase),

        'Template': template.Template,
        'RsrcDef': template.RsrcDef,
        'GetRes': template.GetRes,
        'GetAtt': template.GetAtt,

        'engine': procs.engine,
        'converger': procs.converger,
    }


def main(scenarios_dir='scenarios'):
    if not logging.root.handlers:
        setup_log(logging.root)

    logger = logging.getLogger(__name__)

    from . import processes
    from .framework import datastore
    from .framework import scenario

    for runner in scenario.Scenario.load_all(scenarios_dir):
        try:
            procs = processes.Processes()
            runner(procs.event_loop, **scenario_globals(procs))
        except Exception as exc:
            logger.exception('Exception in scenario "%s"', runner.name)
        finally:
            datastore.Datastore.clear_all()

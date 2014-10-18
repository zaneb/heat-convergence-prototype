import logging


def setup_log(logger):
    log_handler = logging.StreamHandler()
    log_handler.setLevel(logging.DEBUG)

    log_formatter = logging.Formatter('%(levelname) -8s %(name)s: %(message)s')
    log_handler.setFormatter(log_formatter)

    logger.addHandler(log_handler)
    logger.setLevel(logging.DEBUG)


def main():
    if not logging.root.handlers:
        setup_log(logging.root)

    from . import processes
    from . import template

    example_template = template.Template({
        'A': template.RsrcDef({}, []),
        'B': template.RsrcDef({}, []),
        'C': template.RsrcDef({}, ['A', 'B']),
        'D': template.RsrcDef({'c': template.GetRes('C')}, []),
        'E': template.RsrcDef({'ca': template.GetAtt('C', 'a')}, []),
    })
    processes.engine.create_stack('foo', example_template)

    processes.event_loop()

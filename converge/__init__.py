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

    processes.engine.create_stack('foo')

    processes.event_loop()

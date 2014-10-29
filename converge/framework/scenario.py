import os
import logging


logger = logging.getLogger('scenario')


def list_all(directory):
    if not os.path.isdir(directory):
        logger.error('Scenario directory "%s" not found', directory)
        return

    for root, dirs, files in os.walk(directory):
        for filename in files:
            name, ext = os.path.splitext(filename)
            if ext == '.py':
                logger.debug('Found scenario "%s"', name)
                yield name, os.path.join(root, filename)


class Scenario(object):

    @classmethod
    def load_all(cls, directory):
        for name, path in list_all(directory):
            yield cls(name, path)

    def __init__(self, name, path):
        self.name = name

        with open(path) as f:
            source = f.read()

        self.code = compile(source, path, 'exec')
        logger.debug('Loaded scenario %s', self.name)

    def __call__(self, _event_loop, **global_env):
        logger.info('*** Beginning scenario "%s"', self.name)

        exec(self.code, global_env, {})
        _event_loop()

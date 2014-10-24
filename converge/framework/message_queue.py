import collections


Message = collections.namedtuple('Message', ['name', 'data'])


class MessageQueue(object):
    def __init__(self, name):
        self.name = name
        self._queue = collections.deque()

    def send(self, name, data=None):
        self._queue.append(Message(name, data))

    def send_priority(self, name, data=None):
        self._queue.appendleft(Message(name, data))

    def get(self):
        try:
            return self._queue.popleft()
        except IndexError:
            return None

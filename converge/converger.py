from .framework import process


class Converger(process.MessageProcessor):
    def __init__(self):
        super(Converger, self).__init__('converger')

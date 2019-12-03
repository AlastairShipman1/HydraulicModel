import Models
import config
import GlobalClasses

class Transition():
    def __init__(self, max_flow_rate):
        self.max_flow_rate=max_flow_rate


class Door(Transition):
    'check'

import config

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
class Global_timer(metaclass=Singleton):

    def __init__(self):
        self.global_time=0

    def step_time(self):
        self.global_time+=config.timestep


class Global_logger(metaclass=Singleton):
    def __init__(self):
        self.log=[]

    def add_entry(self, entry):
        self.log.append(entry)

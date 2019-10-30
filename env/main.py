import numpy as np


class Global_timer():

    def __init__(self):
        self.global_time=0

    def step_time(self):
        self.global_time+=1


class Element():
    #placeholder class for your destinations
    max_flows={}
    def __init__(self, length, width, population, tread=None, riser=None):
        self.length=length
        self.width=width
        self.type=type
        if self.type=="Staircase":
            self.tread=tread
            self.riser=riser
        self.population=population
        self.max_flow=max_flows[width]
        self.timer=0

    def define_entrypoint(self, entrypoint:Destination):
        self.entrypoint=entrypoint

    def define_exitpoint (self, exitpoint:Destination):
        self.exitpoint=exitpoint
    def step_time(self):
        self.check_global_time()
        self.check_inflows()
        self.check_outflows()
        self.refresh_variables()
        self.timer+=1

    def check_global_time(self):
        'check timing relative to global timer'
    def check_inflows(self):
        'do something'
    def check_outflows(self):
        'check outflows'#


    print("This is a destination")


class Door(Element):

class Outdoors (Element):
    def __init__(self):
        self.width=np.inf
        self.length=np.inf
        self.max_flow=np.inf
        self.area=np.inf
        self.population=np.inf

class Room(Element):

class Corridor(Destination):
    max_flows={}
    def __init__(self, length, width, area, population, entrypoint: Destination, exitpoint: Destination):
        self.length=length
        self.width=width
        self.area=area
        self.population=population
        self.entrypoint=entrypoint
        self.exitpoint=exitpoint
        self.max_flow=max_flows[width]

class Staircase(Element):
    'check'


def step_time(environment, timestep):
    for element in environment:
        element.step_time()


environment=[]
room=Room(10, 10, 100)
stairs=Staircase(10, 10, 0, 1, 1)
corridor=Corridor(20, 2, 0)
door=Door()
outdoors=Outdoors()


environment.append(Room())
environment.append()

import numpy as np
from collections import deque

'''
Please note we will be using metric units wherever possible, and where not possible it will be noted clearly

This model will output a traversal time for an arbitrary collection of elements
These elements will all be connected, eventually, to the outside. All exit routes are specified in advance.
The assumption is that all people immediately walk down their specified route, at predetermined velocity/density relationships
Queuing is accommodated.

need to make sure we can understand dominance of staircases over doors?

The hydraulic model (is this first order or second order?)

1) Set up a group of people, defined by number, density and location (an element).
2) They then start moving towards the first transition (e.g. a door to another room), which leads to the next element
3) Their movement speed is determined by the location and density, the time to transition is determined by the speed.
4) Once at the transition, we need to understand the density on both sides of the transition, which is found by solving a quadratic
4.1) You know the flow rate into the transition, and using F=kD(1-aD)We, we can solve for D
5) Once you have D on the otherside of the transition, you can find S=k-akD, and therefore the time to traverse the next element.
6) If the flow rate is limited (by a door, or the Fmax of the element), then the max flow rate is limited. 
6.1) If the flow rate through a transition is lower than through the element, then queuing occurs. The length of this queue needs to be tracked
7) Each person in the group of people needs to be an object with a counter for how long they have been moving in the element they are in
7.1) Need to adapt this for queuing
'''

class Element():
    #placeholder class for your destinations
    max_flows={}
    boundary_layers={'Stairs':0.15 , 'Handrail':0.98, 'Chair':0, 'Corridor':0.2, 'Obstacles':0.1, 'Concourse':0.46,'Door':0.15}

    def __init__(self, name, length, width, element_type, population, global_logger:Global_logger, global_timer:Global_timer, boundary_layer1=None, boundary_layer2=None, tread=None, riser=None):
        self.name=name
        self.length=length
        self.width=width-boundary_layers[boundary_layer1]-boundary_layers[boundary_layer2] #this is effective width. will it being Nonetype present an issue?
        self.area=self.length*self.width
        self.type=element_type
        self.global_timer=global_timer
        self.global_logger=global_logger
        self.time = 0

        # it would be easy enough to change this to a population of agents, each a class of person, with travel speed etc.
        self.people=deque
        self.population = population
        self.max_population = np.inf  # we should define the max population density, and then calculate the max element population
        self.outflow=0
        self.inflow=0
        # here we have to define the max inflow and outflow of each element.
        self.max_inflow=np.inf
        self.max_outflow=np.inf

        self.possible_queuing=False
        self.queuing=False
        self.queue_length=0

        self.max_speed=1.19 # m/s
        self.max_flow_rate=1.3*self.width #ppl/s/m per unit effective width * effective width
        self.k=1.4
        self.a=0.266
        self.density=0
        self.speed=0


        if self.type=="Staircase":
            self.tread=tread
            self.riser=riser
            # it would also be easy to just look things up in a table, no?
            self.max_speed=0.941-0.066667*self.riser+0.0416667*self.tread #values from regression performed on data
            self.k=0.45-0.2*self.riser+0.07*self.tread #same again
            self.max_flow_rate=0.271667-0.006667*self.riser+0.071667*self.tread #and here

    #implement basic functions for speed, density, flow rate
    def get_speed(self):
        return self.speed

    def set_speed(self):
        self.speed=self.k-self.a*self.k*self.density

    def get_density(self):
        return self.density

    def set_density_given_inflow(self):
        a=self.a*self.k*self.width
        b=-self.k*self.width
        c=self.inflow
        x1=(-b -np.sqrt(b**2-4*a*c))/(2*a)
        x2=(-b +np.sqrt(b**2-4*a*c))/(2*a)
        self.density=min(x1, x2)

    def set_initial_density(self, density):
        self.density=density

    def set_traversal_time(self):
        if self.density==0:
            raise Exception
        else:
            speed=self.get_speed()
            self.traversal_time=self.length/speed

    def calc_current_flow_rate(self):
        if self.population==0:
            self.calc_flow=0
        speed=self.get_speed()
        density=self.get_density()
        calc_flow=self.k*density*self.width*(1-self.a*density)
        self.calc_flow=min(calc_flow, self.max_flow_rate)

    def get_current_flow_rate(self):
        self.calc_flow_rate()
        return self.calc_flow

    def set_inflow_point(self, inflow_point:Element):
        self.inflow_point=inflow_point

    def set_outflow_point(self, outflow_point:Element):
        self.outflow_point=outflow_point

    def get_inflow_rate(self):
        return self.inflow

    def set_inflow_rate(self):
        inflow_element=self.inflow_point
        self.inflow=min(self.max_flow_rate, inflow_element.outflow)

    def set_outflow(self):
        outflow_element=self.outflow_point
        self.outflow=min(self.calc_flow, outflow_element.max_flow_rate)
        if self.calc_flow<outflow_element.max_flow_rate:
            self.possible_queuing=True
            if self.calc_flow>0:
                self.start_queue_tracker()

    def get_outflow(self):
        return self.outflow

    def start_queue_tracker(self):
        if self.already_tracking:
            return
        else:
            self.already_tracking=true
            self.queue_length+=self.calc_flow-self.outflow


class Outdoors():
    def __init__(self):
        ' we need to ensure that all the required variables from elements exitpoints are covered here. how to future proof this?'
        self.width=np.inf
        self.length=np.inf
        self.max_flow=np.inf
        self.area=np.inf
        self.population=0 # done here to ensure the density is always zero
class Corridor(Element):
    'also aisle, ramp, doorway'
class Staircase(Element):
    'check'
class Door(Element):
    'check'

# class used to keep track of the time in each element. can we create this as a singleton class?
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
        self.global_time+=1
class Global_logger(metaclass=Singleton):
    def __init__(self):
        self.log=[]

    def add_entry(self, entry):
        self.log.append(entry)


'''
so we start by defining the environment, and the density of the group of people.
then we start them off on the evacuation route.
'''
environment=[]

stairs=Staircase()
corridor=Corridor()
door=Door()
outdoors=Outdoors()


stairs.define_exitpoint(corridor)
corridor.define_entrypoint(stairs)
corridor.define_exitpoint(door)
door.define_entrypoint(corridor)
door.define_exitpoint(outdoors)

environment.append(room, stairs, corridor, door)


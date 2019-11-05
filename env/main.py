import numpy as np

'''
Please note we will be using metric units wherever possible, and where not possible it will be noted clearly

This model will output an evacuation time for an arbitrary collection of elements
These elements will all be connected, eventually, to the outside. All exit routes are specified in advance.
The assumption is that all people immediately walk down their specified route, at predetermined velocity/density relationships
Queuing is accommodated.

need to make sure we can understand dominance of staircases over doors?

'''


'''
The hydraulic model (is this first order or second order?)

1) Set up a group of people, defined by number, density and location (an element).
2) They then start moving towards the first transition (e.g. a door to another room), which leads to the next element
3) Their movement speed is determined by the location and density, the time to transition is determined by the speed.
4) Once at the transition, we need to understand the density on both sides of the transition, which is found by solving a quadratic
4.1) You know the flow rate into the transition, and using F=kD(1-aD)We, we can solve for D
5) Once you have D on the otherside of the transition, you can find S=k-akD, and therefore the time to traverse the next element.
6) If the flow rate is limited (by a door, or the Fmax of the element), then the max flow rate is limited. 
6.1) If the flow rate through a transition is lower than through the element, then queuing occurs. The length of this queue needs to be tracked

'''


class Person():
    def __init__(self, element):
        self.current_element=element
        self.time_in_element=0

    def step_time(self):
        self.time_in_element+=1

    def change_element(self, element):
        self.current_element=element
        self.time_in_element=0


class Transition():
    'used for doors, entry to staircases, etc'
    boundary_layers = {'Stairs': 0.15, 'Handrail': 0.98, 'Chair': 0, 'Corridor': 0.2, 'Obstacles': 0.1,
                       'Concourse': 0.46, 'Door': 0.15}

    def __init__(self, width, boundary_layer1=None, boundary_layer2=None):
        self.width=width-boundary_layers[boundary_layer1]-boundary_layers[boundary_layer2]
        self.max_speed = 1.19  # m/s
        self.flow_rate = 1.3 * self.width  # ppl/s/m per unit effective width * effective width... unless a staircase!
        self.k = 1.4
        self.a = 0.266
class Door(Transition):
    'stipulate width, type, etc'

    def __init__(self, held_open=False):
        if held_open:
            self.max_flow_rate=50
class StaircaseEntry(Transition):
    'entry to a staircase element'
    def __init__(self, tread, riser):
        self.tread = tread
        self.riser = riser
        self.max_speed = 0.941 - 0.066667 * self.riser + 0.0416667 * self.tread  # values from regression performed on data
        self.k = 0.45 - 0.2 * self.riser + 0.07 * self.tread  # same again
        self.max_flow_rate = 0.271667 - 0.006667 * self.riser + 0.071667 * self.tread  # and here


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


        if self.type=="Staircase":
            self.tread=tread
            self.riser=riser
            self.max_speed=0.941-0.066667*self.riser+0.0416667*self.tread #values from regression performed on data
            self.k=0.45-0.2*self.riser+0.07*self.tread #same again
            self.max_flow_rate=0.271667-0.006667*self.riser+0.071667*self.tread #and here

    def define_entrypoint(self, entry_element:Element, entry_transition: Transition):
        #initially have only one entrypoint. could extend this to multiple fairly easily?
        self.entry_element=entry_element
        self.entry_transition=entry_transition

    def define_exitpoint (self, exit_element:Element, exit_transition:Transition):
        #initially have only one exitpoint. may need to extend this if there is queuing?
        self.exit_element=exit_element
        self.exit_transition=exit_transition

    def step_time(self):
        self.check_global_time()# we need to do something with this- either slow everything else down, or step through everything again
        self.check_current_status()
        self.calc_density_then_velocity()
        self.check_inflows()
        self.check_outflows()
#        self.refresh_variables()
        self.time+=1
        self.initial_flow_timer+=1
        self.check_queuing()


    def check_current_status(self):
        'here we need to check the element has people are queuing, walking or is empty'
        if self.possible_queuing:
            if self.queue_length>0:
                self.queuing=True

        # if queuing, we need to do something about the initial flow timer?
        # we could also highlight that 'here is a bottleneck'?
        #

    def check_global_time(self):
        'check timing relative to global timer'
        if self.time==self.global_timer.global_time:
            return 0
        elif self.time < self.global_timer.global_time:
            return -1
        else:
            return 1

    def start_initial_flow_timer(self):
        'here we do the initial timer for flow through the element'
        self.initial_flow_timer=0
        self.unimpeded_flow_time=self.length/self.max_speed

    def check_inflows(self):
        '''
        add inflow after checking if the population is not too high, then update density
        here we also check if nobody is in the element, and if there is an inflow, we start the initial flow timer
        '''
        if self.population==self.max_population:
            # do we want to do this here/can we actually do it here?
            self.entrypoint.outflow=0
            self.inflow=0
        else:
            self.inflow=self.entrypoint.outflow
            if self.inflow>0 and self.population==0:
                self.start_initial_flow_timer()


    def calc_density_then_velocity(self):
        self.density = self.area/self.population
        self.velocity=self.k-(self.a*self.k*self.density)

    def check_outflows(self):
        '''
        subtrack outflows, after checking that the exitpoint is not full, then update density
        here we also have to check if queuing is occurring, and also the limitation on exit flow rates
        '''

        # if queuing not possible, outflow must be zero.

        if self.exitpoint.population==self.exitpoint.max_population:
            self.outflow=0
        else:
            if not self.possible_queuing:
                self.outflow=0
            else:
                self.flow_rate=self.calculate_predicted_flow()
                '''
                need to implement the flow rate, however they do that
                '''
                self.outflow=min(self.max_flow_rate, self.flow_rate, self.exitpoint.max_inflow)
                if self.outflow<self.flow_rate:
                    self.queue_length+=self.flow_rate-self.outflow
                    self.population-= self.outflow
                    if self.population==0:
                        self.possible_queuing= False
                        self.global_logger.add_entry((self.name, self.global_timer.global_time))
                        # here log the time that this element has emptied.

    def calculate_predicted_flow(self):
        'solve the quadratic using density'
        'this will give F=kD(1-aD)*We'
        calculated_flow=self.k*self.density(1-self.a*(self.density**2))*self.width
        return calculated_flow

    def calculate_transition_outward_flow(self):
        internal_flow=self.calculate_predicted_flow()
        return internal_flow*self.width/self.exitpoint.width

    def calculate_post_transition_density_inward_flow(self):
        a=
        b=
        c=
        x1=(-b -np.sqrt(b**2-4*a*c))/(2*a)
        x2=(-b +np.sqrt(b**2-4*a*c))/(2*a)
        self.density=min(x1, x2, self.max_flow_rate)
        return min(x1, x2)

    def check_queuing(self):
        'this will add to the queues'
        'the time to go from entrypoint to exit point, depending on speed (flow rate)'
        if self.initial_flow_timer > self.unimpeded_flow_time:
            self.possible_queuing=True

class Outdoors (Element):
    def __init__(self):
        self.width=np.inf
        self.length=np.inf
        self.max_flow=np.inf
        self.area=np.inf
        self.population=0 # done here to ensure the density is always zero
class Room(Element):
    'check'
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


def step_time(environment, global_timer, global_logger, timestep):
    for i in range(3):#there are people in the building):
        global_timer.step_time()
        # here we need to randomise the order of the elements in the environment as we cycle through them
        # otherwise, if there is a blockage, one element will never actually evacuate until the other elements have emptied their queues
        # this is only an issue if you have multiple entrypoints
        # and is not an issue if you define where the flows will be coming from (e.g. staircase empties floor by floor)
        for element in environment:
            element.step_time()
    print(global_logger.log)



'''
so we start by defining the environment, and the density of the group of people.
then we start them off on the evacuation route.
'''
gl=Global_logger()
gt=Global_timer()
environment=[]

room=Room(10, 10, 100)
stairs=Staircase(10, 10, 0, 1, 1)
corridor=Corridor(20, 2, 0)
door=Door()

outdoors=Outdoors()

room.define_exitpoint(stairs)
stairs.define_entrypoint(room)
stairs.define_exitpoint(corridor)
corridor.define_entrypoint(stairs)
corridor.define_exitpoint(door)
door.define_entrypoint(corridor)
door.define_exitpoint(outdoors)

environment.append(room, stairs, corridor, door)


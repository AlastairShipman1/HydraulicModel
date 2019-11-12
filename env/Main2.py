import numpy as np
from collections import deque
import config

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
# class used to keep track of the time in each element. can we create this as a singleton class? don't worry about loggers just yet
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

class Element():

    def __init__(self, name, length, width, element_type, population, global_timer:Global_timer, boundary_layer1=None, boundary_layer2=None, tread=None, riser=None):
        boundary_layers = {'Stairs': 0.15, 'Handrail': 0.98, 'Chair': 0, 'Corridor': 0.2, 'Obstacles': 0.1,
                           'Concourse': 0.46, 'Door': 0.15}
        self.name=name
        self.length=length
        self.width=width-boundary_layers[boundary_layer1]-boundary_layers[boundary_layer2] #this is effective width. will it being Nonetype present an issue?
        self.area=self.length*self.width
        self.type=element_type
        self.inflow_transition=None
        self.outflow_transition=None

        #self.global_timer=global_timer
        self.time = 0
        self.flow_timer = 0

        self.outflow=0
        self.inflow=0
        self.calc_flow=0
        # here we have to define the max inflow and outflow of each element.
        self.max_inflow=np.inf
        self.max_outflow=np.inf

        self.position_of_front=0
        self.position_of_back=0

        '''
        This updates in fractional seconds, defined by config.timestep
        '''
        self.max_speed=1.19*config.timestep # m/s
        self.max_flow_rate=1.3*self.width*config.timestep #ppl/s/m per unit effective width * effective width
        self.k=1.4
        self.a=0.266
        self.density=0
        self.density_holder=0
        self.speed=0
        self.unimpeded_traversal_time = self.length / self.max_speed

        if self.type=="Staircase":
            staircase_riser_k={7.5:1, 7:1.08, 6.5:{12:1.16, 13:1.23}}
            staircase_riser_fsm={7.5:1, 7:1.08, 6.5:{12:1.16, 13:1.23}}
            staircase_riser_max_speed={7.5:1, 7:1.08, 6.5:{12:1.16, 13:1.23}}

            self.tread=tread
            self.riser=riser
            if self.riser==6.5:
                self.max_speed=staircase_riser_max_speed[self.riser][self.tread]
                self.k=staircase_riser_k[self.riser][self.tread]
                self.max_flow_rate=staircase_riser_fsm[self.riser][self.tread]
            else:
                self.max_speed=staircase_riser_max_speed[self.riser]
                self.k=staircase_riser_k[self.riser]
                self.max_flow_rate=staircase_riser_fsm[self.riser]
            # it would also be easy to just look things up in a table, no?... the regression values work on arbitrary stairs...
            #self.max_speed=(0.941-0.066667*self.riser+0.0416667*self.tread) *config.timestep #values from regression performed on data
            #self.k=0.45-0.2*self.riser+0.07*self.tread #same again
            #self.max_flow_rate=(0.271667-0.006667*self.riser+0.071667*self.tread) *config.timestep #and here

        self.queue_length = 0
        self.population = population
        self.possible_queuing = False
        self.queuing = False

        # need to implement a queue for the population, to make sure that it is first in first out.
        # self.people = deque
        self.max_population = np.inf  # we should define the max population density, and then calculate the max element population
        self.set_speed()
        self.set_traversal_time()

    def increment_flow_timer(self):
        self.flow_timer += config.timestep

    #implement basic functions for speed, density, flow rate
    def step_time(self):
        'each timestep, we need to check how many people are coming into the element, how many people are leaving, whether people have got to point of leaving'
        ' if there is a queue, whether it decreases in length or increases in length'

        if self.population>0:
            self.calc_current_flow_rate()
            self.check_front_of_group()
            self.check_back_of_group()

        pop_entering=self.check_people_are_entering()


        if self.position_of_front==1 and self.population>0:
            self.set_outflow()

        # this sets the inflow rate, and the density of the resulting flow in this element
        if pop_entering:
            self.set_inflow_rate()
            self.set_density_given_inflow()

        #however, this will only work if there is only one group, and they remain at the same density during the entire
        # flow.
        # if you want multiple groups, you'll need to implement a set_density function.
        # more likely, just implement an agent based model, that keeps individuals in groups, and sets the local density
        # of each individual and thus their movement speed/ the flow rate of the group. these groups can span multiple elements,
        # and then will need to be able to track which elements they are in.

        # this is going to be fun.

        self.update_population_tracker()
        self.time+=config.timestep
        if self.population>0:
            self.flow_timer += config.timestep

    def check_front_of_group(self):
        #as a proportion of the length of the element.
        absolute_position_of_front=self.position_of_front*self.length
        absolute_position_of_front +=self.speed*config.timestep

        self.position_of_front=min(1, absolute_position_of_front/self.length)
        if self.position_of_front>0.95:
            self.possible_queuing=True

    def check_back_of_group(self):
        if self.population==0:
            self.position_of_back=0
        else:
            #as a proportion of element length
            group_length=(self.population/(self.density*self.width))/self.length
            print('group length', group_length)
            self.position_of_back=max(0, self.position_of_front-group_length)

    def check_people_are_exiting(self):
        'check people are in the element, and they have got to the exit point. if they are, then self.possible_queueing=True, and return true'
        if self.flow_timer>self.unimpeded_traversal_time:
            self.possible_queuing=True
        if self.possible_queuing:
            return True
        else:
            return False

    def check_people_are_entering(self):
        'check people in the entry point are ready to enter, if they are, then return true'
        if self.inflow_point==self:
            return False
        else:
            return self.inflow_point.possible_queuing

    def get_speed(self):
        return self.speed

    def set_speed(self):
        self.speed=self.k-self.a*self.k*self.density

    def get_density(self):
        return self.density

    def set_density_given_inflow(self):
        if self.inflow==0:
            return
        else:
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
            return np.inf
        else:
            speed=self.get_speed()
            self.traversal_time=self.length/speed

    def calc_current_flow_rate(self):
        speed=self.get_speed()
        density=self.get_density()
        calc_flow=self.k*density*self.width*(1-self.a*density)
        self.calc_flow=min(calc_flow, self.max_flow_rate)

    def get_current_flow_rate(self):
        self.calc_current_flow_rate()
        return self.calc_flow

    def set_inflow_point(self, inflow_point, inflow_transition=None):
        if inflow_point==self:
            self.inflow=0
        self.inflow_point=inflow_point
        if inflow_transition is not None:
            self.inflow_transition=inflow_transition

    def set_outflow_point(self, outflow_point, outflow_transition=None):
        self.outflow_point=outflow_point
        if outflow_transition is not None:
            self.outflow_transition=outflow_transition

    def get_inflow_rate(self):
        return self.inflow

    def set_inflow_rate(self):
        inflow_element=self.inflow_point
        if inflow_element.population==0:
            self.inflow=0
            return
        if self.inflow_transition:
            self.inflow=min(self.max_flow_rate, self.inflow_transition.max_flow_rate, inflow_element.outflow)
        elif self.inflow_point.name==self.name:
            # it turns out this is inaccessible if we code properly, as this function will never be called for a
            # population source.
            self.inflow=0
        else:
            self.inflow=min(self.max_flow_rate, inflow_element.outflow)

    def set_outflow(self):
        outflow_element=self.outflow_point
        if self.outflow_transition is not None:
            self.outflow=min(self.calc_flow, self.outflow_transition.max_flow_rate, outflow_element.max_flow_rate)
        else:
            self.outflow = min(self.calc_flow, outflow_element.max_flow_rate)

    def get_outflow(self):
        return self.outflow

    def update_population_tracker(self):
        ' here we access a class called population tracker, which checks the length of the queue relative to population etc'
        self.population+=self.inflow
        self.population-=self.outflow
        if self.population<0:# and self.position_of_back>0.95:
            self.population=0
            self.outflow=0
            self.position_of_back=0
            self.flow_timer=0


        #these two can be combined.. think about this later
        #here we check the queue length, and edit it
        if self.queue_length > 0:
            self.queue_length -= self.outflow
            if self.queue_length < 0:
                self.possible_queuing = False
                self.queue_length = 0

        #here we initialise the queues
        if self.calc_flow > self.outflow_point.max_flow_rate:
            self.possible_queuing = True
            if self.calc_flow > 0:
                self.queue_length += (self.calc_flow-self.outflow)

class Transition():
    def __init__(self, max_flow_rate):
        self.max_flow_rate=max_flow_rate

class Outdoors():
    def __init__(self):
        ' we need to ensure that all the required variables from elements exitpoints are covered here. how to future proof this?'
        self.width=np.inf
        self.length=np.inf
        self.max_flow_rate=np.inf
        self.area=np.inf
        self.population=0 # done here to ensure the density is always zero
class Corridor(Element):
    'also aisle, ramp, doorway'
class Staircase(Element):
    'check'
class Door(Transition):
    'check'

def step_time(environment, global_timer):
    global_timer.step_time()
    # here we need to randomise the order of the elements in the environment as we cycle through them
    # otherwise, if there is a blockage, one element will never actually evacuate until the other elements have emptied their queues
    # this is only an issue if you have multiple entrypoints
    # and is not an issue if you define where the flows will be coming from (e.g. staircase empties floor by floor)
    for element in environment:
        element.step_time()
        print('time', global_timer.global_time)
        print('element name', element.name)
        print('element_speed', element.speed)
        print('element_k', element.k)
        print('element_a', element.a)
        print('element_density', element.density)
        print(element.name + "\t popul: {0:9.2f} \t outf: {1:9.2f} \t infl: {2:9.2f} \t front: {3:9.2f} \t back : {4:9.2f}".format(element.population, element.outflow, element.inflow, element.position_of_front, element.position_of_back))




'''
so we start by defining the environment, and the density of the group of people.
then we start them off on the evacuation route.
'''
environment=[]
global_timer=Global_timer()

stairs=Staircase(name='stairs', length=3.31, width=1.8, element_type='Staircase', population=50, global_timer=global_timer, boundary_layer1='Stairs', boundary_layer2='Stairs', tread=11, riser=7)
corridor=Corridor(name='corridor', length=10, width=1.8, element_type='Corridor', population=0, global_timer=global_timer, boundary_layer1='Corridor', boundary_layer2='Corridor')
#corridor2=Corridor(name='corridor2', length=10, width=1.8, element_type='Corridor', population=0, global_timer=global_timer, boundary_layer1='Corridor', boundary_layer2='Corridor')
#corridor3=Corridor(name='corridor3', length=10, width=1.8, element_type='Corridor', population=0, global_timer=global_timer, boundary_layer1='Corridor', boundary_layer2='Corridor')
#corridor4=Corridor(name='corridor4', length=10, width=1.8, element_type='Corridor', population=0, global_timer=global_timer, boundary_layer1='Corridor', boundary_layer2='Corridor')


door=Door(1.3*config.timestep)
door2=Door(np.inf)
#door3=Door(np.inf)
#door4=Door(np.inf)
outdoors=Outdoors()


stairs.set_inflow_point(stairs)
stairs.set_outflow_point(corridor, door2)
stairs.set_initial_density(1.5)
corridor.set_inflow_point(stairs, door2)
corridor.set_outflow_point(outdoors, door)


'''
corridor2.set_inflow_point(corridor, door)
corridor2.set_outflow_point(corridor3, door2)

corridor3.set_inflow_point(corridor2, door2)
corridor3.set_outflow_point(outdoors, door3)

corridor4.set_inflow_point(corridor3, door3)
corridor4.set_outflow_point(outdoors, door4)
'''
environment.append(stairs)
environment.append(corridor)
#environment.append(corridor3)
#environment.append(corridor4)

def check_people_in_building(environment):
    population=0
    for element in environment:
        population+=element.population
    if population>0:
        return True
    else:
        return False

people_in_building=True
while(people_in_building):
    step_time(environment, global_timer)
    people_in_building=check_people_in_building(environment)


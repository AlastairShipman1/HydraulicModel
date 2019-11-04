import numpy as np

'''
Please note we will be using metric units wherever possible, and where not possible it will be noted clearly
'''
class Global_timer():

    def __init__(self):
        self.global_time=0

    def step_time(self):
        self.global_time+=1

class Element():
    #placeholder class for your destinations
    max_flows={}
    boundary_layers={'Stairs':0.15 , 'Handrail':0.98, 'Chair':0, 'Corridor':0.2, 'Obstacles':0.1, 'Concourse':0.46,'Door':0.15}

    def __init__(self, length, width, element_type, population, global_timer:Global_timer, boundary_layer1=None, boundary_layer2=None, tread=None, riser=None):
        self.length=length
        self.width=width-boundary_layers[boundary_layer1]-boundary_layers[boundary_layer2] #this is effective width. will it being Nonetype present an issue?
        self.area=self.length*self.width
        self.type=element_type
        self.global_timer=global_timer
        self.time = 0

        self.population = population
        self.max_population = np.inf  # we should define the max population density, and then calculate the max element population
        self.outflow=0
        self.inflow=0
        self.max_inflow=np.inf
        self.max_outflow=np.inf
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

    def define_entrypoint(self, entrypoint:Destination):
        #initially have only one entrypoint. could extend this to multiple fairly easily?
        self.entrypoint=entrypoint

    def define_exitpoint (self, exitpoint:Destination):
        #initially have only one exitpoint. may need to extend this if there is queuing?
        self.exitpoint=exitpoint

    def step_time(self):
        self.check_global_time()# we need to do something with this- either slow everything else down, or step through everything again
        self.check_current_status()
        self.check_inflows()
        self.check_outflows()
        self.refresh_variables()
        self.time+=1
        self.initial_flow_timer+=1

    def check_current_status(self):
        'here we need to check the element has people are queuing, walking or is empty'

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

        if self.exitpoint.population==self.exitpoint.max_population:
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

    def calculate_predicted_flow(self):
        'solve the quadratic using density'
        'this will give Fs'
        return self.velocity*self.area # this isn't right, is it?

    def move_through_element(self):
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
        self.population=np.inf
class Room(Element):
    'check'
class Corridor(Element):
    'also aisle, ramp, doorway'
    def __init__(self):
        self.a=0.266
        self.k=1.4
class Staircase(Element):
    'check'
class Door(Element):
    'check'


def step_time(environment, global_timer, timestep):
    global_timer.step_time()
    for element in environment:
        element.step_time()

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


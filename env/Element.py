import Models
import config
import numpy as np
from GlobalClasses import Global_timer, Global_logger

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
        self.inflow_point=None
        self.inflow_points=None

        self.time = 0
        self.flow_timer = 0


        '''
        This updates in fractional seconds, defined by config.timestep
        '''
        self.max_speed=1.19*config.timestep # m/timestep
        self.max_flow_rate=1.3*self.width*config.timestep #ppl/s/m per unit effective width * effective width
        self.k=1.4
        self.a=0.266
        self.density=0
        self.density_holder=0
        self.speed=0
        self.unimpeded_traversal_time = self.length / self.max_speed # in config.timesteps

        if self.type=="Staircase":
            staircase_riser_k={7.5:1, 7:1.08, 6.5:{12:1.16, 13:1.23}}
            staircase_riser_fsm={7.5:1, 7:1.08, 6.5:{12:1.16, 13:1.23}}
            staircase_riser_max_speed={7.5:1, 7:1.08, 6.5:{12:1.16, 13:1.23}}

            self.tread=tread
            self.riser=riser
            if self.riser==6.5:
                self.max_speed=staircase_riser_max_speed[self.riser][self.tread]
                self.k=staircase_riser_k[self.riser][self.tread]
                self.max_flow_rate=staircase_riser_fsm[self.riser][self.tread]*self.width
            else:
                self.max_speed=staircase_riser_max_speed[self.riser]
                self.k=staircase_riser_k[self.riser]
                self.max_flow_rate=staircase_riser_fsm[self.riser]*self.width

            self.max_speed*=config.timestep #m/config.timestep
            self.max_flow_rate*=config.timestep #ppl/config.timestep

            # can do this either by regression or by looking up in a dict (as we currently do)... the regression values work on arbitrary stairs...
            # need to check these regression values.
            #self.max_speed=(0.941-0.066667*self.riser+0.0416667*self.tread) *config.timestep #values from regression performed on data
            #self.k=0.45-0.2*self.riser+0.07*self.tread #same again
            #self.max_flow_rate=(0.271667-0.006667*self.riser+0.071667*self.tread) *config.timestep #and here


        self.outflow=0
        self.inflow=0
        self.calc_flow=0
        # here we have to define the max inflow and outflow of each element.
        self.max_inflow=self.max_flow_rate
        self.max_outflow=self.max_flow_rate

        self.position_of_front=0
        self.position_of_back=0

        self.queue_length = 0
        self.population = population
        self.possible_queuing = False
        self.queuing = False
        self.queue_population=0


        # need to implement a queue for the population, to make sure that it is first in first out. DO THIS IN 'GROUP' OBJECTS INSTEAD
        # self.people = deque
        self.max_population = np.inf  # we should define the max population density, and then calculate the max element population
        self.set_speed()
        self.set_traversal_time()

    def increment_flow_timer(self):
        self.flow_timer += config.timestep
    #implement basic functions for speed, density, flow rate
    def step_time(self):
        'each timestep, we need to check how many people are coming into the element, how many people are leaving, whether people have got to point of leaving'
        'if there is a queue, whether it decreases in length or increases in length'

        'RENAME THIS TO PROVISIONAL INFLOW OUTFLOWS?'
        'BECAUSE FOR THE MULTIPLE INFLOWS WE NEED TO ENSURE THAT ALL ELEMENTS COMMUNICATE'

        #you need to check on the order of these things:
            # check inflow, check outflow, calc_flow_rate
            # correlate between elements that this all works, and if not, override.

            # then, once it has all been coordinated
            # check queue length, update population

            # Maybe just move the population tracker to a different function?


        if self.population>0:
            self.check_front_of_group()
            self.check_back_of_group()

        self.calc_current_flow_rate()

        if self.position_of_front==1 and self.population>0:
            self.set_outflow()

        # this sets the inflow rate, and the density of the resulting flow in this element
        pop_entering=self.check_people_are_entering()
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
        absolute_position_of_front +=self.speed

        self.position_of_front=min(1, absolute_position_of_front/self.length)
        if self.position_of_front>0.95:
            self.possible_queuing=True

    def check_back_of_group(self):
        if self.population==0:
            self.position_of_back=0
        else:
            #as a proportion of element length
            group_length=(self.population/(self.density*self.width))/self.length
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
        if self.inflow_points:
            for element in self.inflow_points:
                return element.possible_queuing
        else:
            if self.inflow_point==self:
                return False
            else:
                return self.inflow_point.possible_queuing

    def get_speed(self):
        return self.speed

    def set_speed(self):
        self.speed=(self.k-self.a*self.k*self.density)*config.timestep #movement speed per unit timestep

    def get_density(self):
        return self.density

    def set_density_given_inflow(self):
        if self.inflow==0:
            return
        else:
            a=1
            b=-1/self.a
            c=self.inflow/(self.a*self.k*self.width*config.timestep)# needs to be independent of timestep
            x1=(-b -np.sqrt(b**2-4*a*c))/(2*a)
            x2=(-b +np.sqrt(b**2-4*a*c))/(2*a)
            self.density=min(x1, x2)
            self.set_speed()

    def set_initial_density(self, density):
        self.density=density
        self.set_speed()

    def set_traversal_time(self):
        if self.density==0:
            return np.inf
        else:
            speed=self.get_speed()
            self.traversal_time=self.length/speed

    def calc_current_flow_rate(self):

        if self.inflow>0:
            self.calc_flow=self.inflow
        else:
            if self.population>0:
                speed=self.get_speed()
                density=self.get_density()
                calc_flow=self.k*density*self.width*(1-self.a*density)*config.timestep
                self.calc_flow=min(calc_flow, self.max_flow_rate)
            else:
                self.calc_flow=0

    def get_current_flow_rate(self):
        #self.calc_current_flow_rate()
        return self.calc_flow

    def set_inflow_point(self, inflow_point, inflow_transition=None):
        #right: how do we make this work for multiple inflow points?
        if inflow_point==self:
            self.inflow=0
        if type(inflow_point) is list:
            self.inflow_points=inflow_point
        else:
            self.inflow_point=inflow_point
        if inflow_transition is not None:
            self.inflow_transition=inflow_transition

    def set_outflow_point(self, outflow_point, outflow_transition=None):
        #must only be single outflow point? otherwise need to keep track of inflows and outflows and agents.
        self.outflow_point=outflow_point
        if outflow_transition is not None:
            self.outflow_transition=outflow_transition

    def get_inflow_rate(self):
        return self.inflow

    def set_inflow_rate(self):
        #create a list of currently outflowing points, and then split up their flow by their relative widths?: this is
        # only if they access the same point.
        # if they are in a corridor and enter different points, you will have to split the corridor into sub corridors.
        #then you need to limit their inflow by the same method as before (in proportion to each other)
        # then you need to back update them to make sure that they don't still think their flow rate is whatever it is.....

        if self.inflow_points is not None:
            currently_inflowing_points=[]
            total_max_flow_rates=0
            total_inflow=0
            for element in self.inflow_points:
                if element.outflow>0:
                    currently_inflowing_points.append(element)
                    total_inflow+=element.outflow
                    if element.outflow_transition:
                        total_max_flow_rates += min(element.max_flow_rate, element.outflow_transition.max_flow_rate)
                    else:
                        total_max_flow_rates +=element.max_flow_rate
            #so now we have a list of the elements flowing in

            'this does not check for inflow.transition, as below. you have transitions between each element, so there is no "one" inflow transition'
            self.inflow=min(self.max_flow_rate, total_inflow)
            if self.inflow<total_inflow:
                for element in currently_inflowing_points:
                    #here we rescale the outflow of each inflow_point, so that they add up to the max that this element can take.
                    #they are scaled proportionally by their maximum flow rates. this is an optimistic outcome.
                    scaler=self.inflow*(min(element.max_flow_rate, element.outflow_transition.max_flow_rate))/total_max_flow_rates
                    element.override_outflow(scaler)

        else:
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

    def override_outflow(self, outflow):
        self.outflow=outflow

    def update_population_tracker(self):
        ' here we access a the population tracker, which checks the current population of the element, and any associated queues'
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

        #here we initialise the queues THIS DOESN'T WORK, BECAUSE OUTFLOW/INFLOW RATES ARE RECOMPUTED BETWEEN ELEMENTS.
        # SO WE NEED TO UPDATE QUEUE LENGTH AFTER THIS.
        if self.calc_flow > self.outflow:
            self.possible_queuing = True
            if self.outflow > 0:
                self.queue_population += (self.calc_flow-self.outflow)

class Corridor(Element):
    'also aisle, ramp, doorway'
class Staircase(Element):
    'check'
class Room(Element):
    'check'

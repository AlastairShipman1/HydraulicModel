import numpy as np
import collections
import config
import Element
import Transition
# class used to keep track of the time in each element. can we create this as a singleton class? don't worry about loggers just yet


class Outdoors():
    def __init__(self):
        ' we need to ensure that all the required variables from elements exitpoints are covered here. how to future proof this?'
        self.width=np.inf
        self.length=np.inf
        self.max_flow_rate=np.inf
        self.area=np.inf
        self.population=0 # done here to ensure the density is always zero

class Floor():
    'made up of elements. is this sensible?'
    'each floor makes it into a building.'
class Building():
    'made up of floors. is this sensible?'
    'has a total population. run "step_time" through this building '
    def __init__(self, building):
        self.building=building

    def step_time(self):
        for element in self.building:
            element.step_time()

class Person():
    'each person should belong to a group, should be in an element, should have a speed'
    'you should be able to change most of these'

    def __init__(self, speed, group=None, element=None):# need to create groups and elements and people, then add, group, element):
        #assert type(group) is Group, "need to ensure the group is a group"
        #assert type(element) is element, "need to ensure the element is an element"
        self.speed=speed
        self.group=group
        self.element=element
        self.next_element= None

    def set_group(self, group):
        self.group=group
        group.add_agent(self)

    def get_group(self):
        return self.group

    def set_speed(self, speed):
        self.speed=speed

    def get_speed(self):
        return self.speed

    def set_element(self, element):
        if not type(element) is Element:
            raise TypeError ("element is not of type(Element)")
        self.element=element
        self.next_element=element.outflow_point

    def move_to_next_element(self):
        self.element=self.next_element
        self.next_element=self.element.outflow_point

    def get_element(self):
        return self.element

    def get_next_element(self):
        return self.next_element

class elementQueue():
    def __init__(self, agents):
        self.queue=collections.deque(agents)

    def remove_agent(self):
        agent=self.queue.pop()
        return agent

    def add_agent(self, agent):
        self.queue.append(agent)

class Group():
    '''
    'what we want to do here is track individual groups as they move through the environment.'
    what we do is initially define the group population, the starting element and the route they will take (a list and a dict of queues)
    then each time that element flows people out of it, it should call the 'flow_discrete_people' function.
    this will then update the locations of each individual in that group.
    '''
    def __init__(self,name, agents=None, element=None):
        self.agents=agents
        if self.agents is not None:
            self.population = len(self.agents)

        self.name=name

    def add_agent(self, agent:Person):
        'Here we can add a person to the group'
        assert type(agent) is Person, 'agent is not a person'
        if self.agents==None:
            self.agents=[]
        if agent not in self.agents:
            self.agents.append(agent)
            self.population=len(self.agents)
            agent_location=agent.get_element().name
            self.route_populations[agent_location]+=1
        else:
            print('Agent already in this group')

    def remove_agent(self, agent:Person):
        assert type(agent) is Person, 'agent is not a person'
        if self.agents==None:
            return
        if agent in self.agents:
            self.agents.remove(agent)
        else:
            print('agent is not in this group')

        if len(self.agents)==0:
            self.agents=None

    def get_agents(self):
        return self.agents

    def _set_initial_element(self, element):
        for agent in self.agents:
            agent.set_element(element)
        self.route_populations[element.name]=len(self.agents)

    def set_initial_path(self, starting_element):
        self.route=[]
        self.route_populations={}
        self.route_queues={}
        self.route_flow_rates={}

        current_element = starting_element
        checking = True
        while checking:
            self.route.append(current_element)
            self.route_queues[current_element.name]=elementQueue()
            self.route_flow_rates[current_element.name]=0
            self.route_populations[current_element.name]=0

            current_element=current_element.outflow_point
            next_element = current_element.outflow_point
            if next_element is type(Outdoors):
                checking=False

        #here we set the initial elements for all the agents, and the initial population of the beginning of the route.
        self._set_initial_element(starting_element)

    def flow_discrete_individuals(self, outflowing_element):
        'Here we want to take the cumulative flow rate from the outflowing element, and once it gets above 1, flow an individual from the group '
        locator=outflowing_element.name
        self.route_flow_rates[locator]+=outflowing_element.outflow
        # assumes flow won't go above 1 person/sec? reasonable for fractional time, or normal corridors. if you have
        # particularly wide doors, with multiple inflows, this might not work.
        if self.route_flow_rates[locator]>1:
            'pop the next person from the deque, change element to next element'
            self.route_flow_rates[locator]-=1
            interim_agent=self.route_queues[outflowing_element.name].pop()
            self.route_queues[outflowing_element.outflow_point].add_agent(interim_agent)


#Basic functions for running the model.
def step_time(environment, global_timer):
    global_timer.step_time()
    # here we need to randomise the order of the elements in the environment as we cycle through them
    # otherwise, if there is a blockage, one element will never actually evacuate until the other elements have emptied their queues
    # this is only an issue if you have multiple entrypoints
    # and is not an issue if you define where the flows will be coming from (e.g. staircase empties floor by floor)
    for element in environment:
        element.step_time()
    for element in environment:
        print('time', global_timer.global_time)
        print('element name', element.name)
        #print('element_speed: m/config.timestep', element.speed)
        print('element_population', element.population)
        #print('element_k', element.k)
        #print('element_a', element.a)
        print('element_calc_flow: ppl/config.timestep', element.calc_flow)
        #print('element_inflow', element.inflow)
        print('element_outflow', element.outflow)
        #print('element_density', element.density)
        #print(element.name + "\t popul: {0:9.2f} \t outf: {1:9.2f} \t infl: {2:9.2f} \t front: {3:9.2f} \t back : {4:9.2f}".format(element.population, element.outflow, element.inflow, element.position_of_front, element.position_of_back))
        print('element.queue pop', element.queue_population)
        print('############################################################################################################')

def check_people_in_building(environment):
    population=0
    for element in environment:
        population+=element.population
    if population>0:
        return True
    else:
        return False



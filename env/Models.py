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

    'what we want to do here is track individual groups as they move through the environment.'
    'this means checking their position, when they start in one element, leave another, the average speed'
    'a reference to each person, a way to add agents, a way to remove agents, etc'
    'update this object everytime outflow is called in "Element" objects '
    'CURRENTLY THIS METHOD ONLY WORKS WHEN A GROUP IS IN TWO ELEMENTS.'
    'NEED TO BE ABLE TO INCREASE THIS TO ARBITRARY elements'

    def __init__(self,name, agents=None, element=None):#, agents:list, current_element:Element):
        #assert type(agents) is list, 'need to input a list of agents'
        self.agents=agents
        if self.agents is not None:
            self.initial_queue=elementQueue(agents)
            self.population = len(self.agents)

        self.name=name
        self.current_element=element
        self.flow_through_elements=0

    def add_agent(self, agent:Person):
        'Here we can add a person to the group'
        assert type(agent) is Person, 'agent is not a person'
        if self.agents==None:
            self.agents=[]
        if agent not in self.agents:
            self.agents.append(agent)
            self.queue.append(agent)
            self.population=len(self.agents)
        else:
            print('Agent already in this group')

    def remove_agent(self, agent:Person):
        assert type(agent) is Person, 'agent is not a person'
        if self.agents==None:
            return
        if agent in self.agents:
            self.agents.remove(agent)
            self.queue.pop(agent)
        else:
            print('agent is not in this group')

        if len(self.agents)==0:
            self.agents=None

    def get_agents(self):
        return self.agents

    def set_initial_element(self, element):
        for agent in self.agents:
            agent.set_element(element)

    def set_current_element(self, element:Element):
        assert type(element) is Element, 'need to input an element'
        # need to be able to override this from the element, once population has dropped to zero?
        # or perhaps completely compartmentalise this, and just keep things in track by the global timer.
        self.current_element=element

    def get_current_elements(self):
        current_elements=[]
        for agent in self.agents:
            if agent.get_element() not in current_elements:
                current_elements.append(agent.get_element())

    def set_next_element(self, element:Element):
        assert type(element) is Element, 'need to input an element'
        self.next_element=element

    def flow_discrete_individuals(self, flow_rate, outflowing_element):
        'Here we want to take the cumulative flow rate from the element, and once it gets above 1, flow an individual from the group '
        'from current element to next element'
        'once the population in current element==0, redefine current and next elements'
        'keep the model below as continuous, as it will remain accurate'
        'however, you will want this bit to be a discrete add-on'
        'you also want a queue of people, so that first in==first out'
        'this currently only allows the group to straddle 2 elements.'
        'you will want this to be scalable to n elements'

        #YOUR ISSUE IS YOU WANT THIS TO HAPPEN AT RUN TIME. IT MIGHT BE THE CASE THAT YOU NEED INSTEAD TO DO THIS FOR THE ENTIRE
        # PATH BEFORE RUNNING.
        # THIS WILL LEAD TO MEMORY LEAK. IT WOULD BE BETTER TO DO IT DYNAMICALLY, BUT WILL THIS WORK?

        self.flow_through_elements+=flow_rate
        if self.flow_through_elements>1:
            'pop the next person from the deque, change element to next element'
            self.flow_through_elements-=1
            interim_agent=self.queue.pop()
            self.interim_queue.append(interim_agent)

        if len(self.queue)==0:
            for agent_number in range(len(self.interim_queue)):
                agent=self.interim_queue.pop()
                self.queue.append(agent)


        # i think you want to get rid of these: the group is defined by the elements of its agents, not the other way around.
        current_pop = self.get_population_in_current_element()
        next_pop = self.get_population_in_next_element()

        if current_pop == 0:
            self.set_current_element(self.next_element)
            next_element=self.next_element.outflow_point
            self.set_next_element(next_element)


    def get_population_in_current_element(self):
        population=0
        for agent in self.agents:
            if agent.current_element==self.current_element:
                population+=1
        return population

    def get_population_in_next_element(self):
        population=0
        for agent in self.agents:
            if agent.current_element==self.next_element:
                population+=1
        return population

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



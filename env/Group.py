import numpy as np
import collections
import config
import Element
import Transition
import GlobalClasses
import Outdoors
import Person
import Models

class elementQueue():
    def __init__(self):
        self.queue=collections.deque()

    def remove_agent(self):
        agent=self.queue.pop()
        return agent

    def add_agent(self, agent):
        self.queue.append(agent)

    def __len__(self):
        return len(self.queue)

class Group():
    '''
     what we want to do here is track individual groups as they move through the environment.
     what we do is initially define the
        group population,
        the starting element (where they all reside)
        and the route they will take (a list and a dict of queues)
     then each config.timestep we call step_time()
        if any agent is in an element that is flowing, it should call the 'flow_discrete_people' function.
        this moves agents from that element to the next, by way of a queue
        if all agents are outdoors, the group then stops updating.

    '''
    def __init__(self,name, global_timer:GlobalClasses.Global_timer, agents=None):
        self.agents=agents
        self.global_timer=global_timer
        if self.agents is not None:
            self.population = len(self.agents)

        self.name=name
        self.start_time=self.global_timer.global_time
        self.updating=True
        self.elements=[]
        self.time=0

    def step_time(self):
        'you will need to make sure that other groups are not also in the element?'
        'because then the outflow needs to be shared across the groups'

        self.elements=self.get_elements()

        self.update_route_population_tracker()
        if self.updating:
            for element in self.elements:
                if element.name is not 'Outdoors':
                    if(self.check_element_is_flowing(element)):
                        self.flow_discrete_individuals(element)
        self.check_group_in_building()
        self.time+=config.timestep

    def add_agent_to_group(self, agent:Person):
        'Here we can add a person to the group'
        if self.agents==None:
            self.agents=[]
        if agent not in self.agents:
            self.agents.append(agent)
            self.population=len(self.agents)
            #agent_location=agent.get_element().name

        else:
            print('Agent already in this group')

    def remove_agent_from_group(self, agent:Person):
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

    def get_elements(self):
        elements=[]
        for agent in self.agents:
            if agent.get_element() not in elements:
                elements.append(agent.get_element())
        return elements

    def _set_initial_element(self, element):
        for agent in self.agents:
            agent.set_element(element)
            self.route_queues[element.name].add_agent(agent)
        self.update_route_population_tracker()

    def update_route_population_tracker(self):
        #reset all populations to zero, then repopulate
        for element in self.route:
            self.route_populations[element.name]=0

        for agent in self.agents:
            self.route_populations[agent.get_element().name]+=1

    def set_initial_path(self, starting_element):
        self.route=[]
        self.route_populations={}
        self.route_queues={}
        self.route_flow_rates={}

        current_element = starting_element
        checking = True
        while checking:
            'might want to put a check in here, saying that paths cannot be longer than 50 elements?'
            next_element = current_element.outflow_point
            self.route.append(current_element)
            self.route_queues[current_element.name]=elementQueue()
            self.route_flow_rates[current_element.name]=0
            self.route_populations[current_element.name]=0

            current_element=current_element.outflow_point

            if current_element.name is 'Outdoors':
                self.route.append(current_element)
                self.route_queues[current_element.name] = elementQueue()
                self.route_flow_rates[current_element.name] = 0
                self.route_populations[current_element.name] = 0
                for element in self.route:
                    print(element.name)
                checking=False

        #here we set the initial elements for all the agents, and the initial population of the beginning of the route.
        self._set_initial_element(starting_element)

    def check_element_is_flowing(self, element):
        if element.outflow>0:
            return True
        else:
            return False

    def flow_discrete_individuals(self, outflowing_element):
        'Here we want to take the cumulative flow rate from the outflowing element, and once it gets above 1, flow an individual from the group '
        locator=outflowing_element.name
        next_locator=outflowing_element.outflow_point.name
        self.route_flow_rates[locator]+=outflowing_element.outflow

        # this seems like a hack. we should be able to update in parallel, but as it is sequential, we need to keep track of things accurate
        # to the value below and to config.timestep.
        if self.route_flow_rates[locator]>0.9:
            'pop the next person from the deque, change element to next element'
            self.route_flow_rates[locator]-=1
            interim_agent=self.route_queues[outflowing_element.name].remove_agent()
            interim_agent.move_to_next_element()
            self.route_queues[outflowing_element.outflow_point.name].add_agent(interim_agent)

    def check_group_in_building(self):
        if len(self.elements)==1:
            if self.elements[0].name=='Outdoors':
                self.group_has_left_building()

    def group_has_left_building(self):
        self.end_time=self.global_timer.global_time
        self.duration=self.end_time-self.start_time
        self.updating=False

    def print_status(self):
        for element in self.elements:
            print('###########################################################################')
            print(self.global_timer.global_time)
            print ('Name: '+element.name)
            print('Element Population: '+str(element.population))
            print('Groupwise element population: ' +str(self.route_populations[element.name]))

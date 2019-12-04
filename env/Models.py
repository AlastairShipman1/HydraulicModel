import numpy as np
import collections
import config
import Element
import Transition
import GlobalClasses
import Group

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


#Basic functions for running the model.
def step_time(environment, global_timer, groups=None):
    global_timer.step_time()
    for element in environment:
        element.step_time()
    '''
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
    '''
    if groups is not None:
        for group in groups:
            group.step_time()
        for group in groups:
            group.print_status()

def check_people_in_building(environment):
    population=0
    for element in environment:
        population+=element.population
    if population>0:
        return True
    else:
        return False



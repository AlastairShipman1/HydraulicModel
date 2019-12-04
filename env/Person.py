import numpy as np
import collections
import config
import Element
import Transition
import GlobalClasses
import Group
import Models


class Person():
    'each person should belong to a group, should be in an element'
    'you should be able to change most of these'
    'do we want to run things from the hydraulic model?, or do we want to run things from here?'
    'Or do we want the option?'
    'If we want the option, then, for agent based models, do we just want to scale speed? if so, how do work out density?'

    'we initially run things as a hydraulic model. if you want to develop further, then focus on it later'

    def __init__(self, group=None, element=None):
        self.group=group
        self.element=element

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
        #if not type(element) is Element:
         #   raise TypeError ("element is not of type(Element)")
        self.element=element
        self.next_element=element.outflow_point

    def move_to_next_element(self):
        self.element=self.next_element
        if not self.element.name == 'Outdoors':
            self.next_element=self.element.outflow_point

    def get_element(self):
        return self.element

    def get_next_element(self):
        return self.next_element

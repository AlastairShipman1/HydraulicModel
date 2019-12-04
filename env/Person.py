import numpy as np
import collections
import config
import Element
import Transition
import GlobalClasses
import Group
import Models


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

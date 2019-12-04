import numpy as np
import collections
import config
import Element
import Transition
import GlobalClasses
import Group


class Outdoors():
    def __init__(self):
        ' we need to ensure that all the required variables from elements exitpoints are covered here. how to future proof this?'
        'we could use an interface, but how does python do this?'
        'should this be a global class?'
        self.name='Outdoors'
        self.width=np.inf
        self.length=np.inf
        self.max_flow_rate=np.inf
        self.area=np.inf
        self.population=0 # done here to ensure the density is always zero

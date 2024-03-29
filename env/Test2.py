'''
###################################################################################################################
Test 2 is a floor from the multiple floor building, building into test 3, the full multiple floor building.

Each floor has a corridor with multiple entrance doors, and 2 exit doors, and 300 people population
Half the population goes to one exit, half goes to the other.
The answer should be:
----- 25.4 minutes for a first order model (full building)
----- 25.3 minutes for a second order model (full building)


create a floor with a population, then create a deepcopy of that floor n times. is this the way to do it?
--- or do we just create a new object of floor, using inputs that are deepcopies?
create the top floor and the bottom floor, and then populate the evacuation route.

###################################################################################################################
'''

import Models
import config
import numpy as np


'''

Each floor has nine rooms either side of the corridor
        #########
        # Room  #
###########  ###################################
Door      |  |       Corridor........ etc:
###########  ###################################
        # Room  #
        #########

It's probably best to split the corridor up into smaller corridors, as indicated by vertical lines? then we have a single element, 
that has 3 inputs (2x rooms, 1x corridor) and 1 exit (corridor). the only thing it does is act as a transition point, but with 
flows from multiple points.

this will not work arbitrarily. need to split elements up when they have multiple entrances, until they cannot be split further.

Then it becomes a mesoscopic network/group based model, with each element having a transition into the next, 

and then each floor connects to a staircase, which has an input of the staircase above it as well (except the top floor)


'''


global_timer=Models.Global_timer()
test_environment1=[]

room=Models.Room(name='room', length=5, width=5, element_type='Room', population=15, global_timer=global_timer, boundary_layer1='door', boundary_layer2='door')

stairs=Models.Staircase(name='stairs', length=3.31, width=1.8, element_type='Staircase', population=50, global_timer=global_timer, boundary_layer1='Stairs', boundary_layer2='Stairs', tread=11, riser=7)
corridor=Models.Corridor(name='corridor', length=40, width=2.4, element_type='Corridor', population=0, global_timer=global_timer, boundary_layer1='Corridor', boundary_layer2='Corridor')

door=Models.Door(1.3*config.timestep)
door2=Models.Door(np.inf)

outdoors=Models.Outdoors()

stairs.set_inflow_point(stairs)
stairs.set_outflow_point(corridor, door2)
stairs.set_initial_density(1.5)
corridor.set_inflow_point(stairs, door2)
corridor.set_outflow_point(outdoors, door)

test_environment1.append(stairs)
test_environment1.append(corridor)


people_in_building=True
while(people_in_building):
    Models.step_time(test_environment1, global_timer)
    people_in_building=Models.check_people_in_building(test_environment1)

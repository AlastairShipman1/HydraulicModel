'''
###########################################################################################################
Test1 is a single floor, made up of a staircase, flowing into a corridor and then a door.
The population is 50, at an initial density of 1.5, all located at the top of the stairs.


---- The total evacuation time should be 53.4s.
---- The time for the group to start exiting the stairs should be 5.1s

need to figure out how to actually run tests.
###########################################################################################################
'''

import Models
import config
import numpy as np


global_timer=Models.Global_timer()
test_environment1=[]

stairs=Models.Staircase(name='stairs', length=3.31, width=1.8, element_type='Staircase', population=50, global_timer=global_timer, boundary_layer1='Stairs', boundary_layer2='Stairs', tread=11, riser=7)
stairs2=Models.Staircase(name='stairs2', length=3.31, width=1.8, element_type='Staircase', population=50, global_timer=global_timer, boundary_layer1='Stairs', boundary_layer2='Stairs', tread=11, riser=7)

corridor=Models.Corridor(name='corridor', length=10, width=1.8, element_type='Corridor', population=0, global_timer=global_timer, boundary_layer1='Corridor', boundary_layer2='Corridor')
door=Models.Door(1.3*config.timestep)
door2=Models.Door(np.inf)
outdoors=Models.Outdoors()

stairs.set_inflow_point(stairs)
stairs.set_outflow_point(corridor, door2)
stairs.set_initial_density(1.5)

stairs2.set_inflow_point(stairs2)
stairs2.set_outflow_point(corridor, door2)
stairs2.set_initial_density(1.5)

inflow_points=[]
inflow_points.append(stairs)
inflow_points.append(stairs2)

corridor.set_inflow_point(inflow_points, door2)
corridor.set_outflow_point(outdoors, door)

test_environment1.append(stairs)
test_environment1.append(stairs2)
test_environment1.append(corridor)


people_in_building=True
while(people_in_building):
    Models.step_time(test_environment1, global_timer)
    people_in_building=Models.check_people_in_building(test_environment1)
print(global_timer.global_time)
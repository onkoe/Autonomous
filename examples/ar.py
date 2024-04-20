from time import sleep
from libs import aruco_tracker

tracker = aruco_tracker.ARTracker([0], write=False) #ARTracker requires a list of camera files

while True:
    tracker.find_marker(1)#, id2 = 1)
    print('Distance (in cm): ', tracker.distance_to_marker)
    print('Angle: ', tracker.angle_to_marker)
    sleep(.5)

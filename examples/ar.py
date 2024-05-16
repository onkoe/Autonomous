from time import sleep
from libs import aruco_tracker
from loguru import logger

tracker = aruco_tracker.ARTracker([0], write=False) # ARTracker requires a list of camera IDs
marker = 1 # change this ARUCO identifier if you need to :)

while True:
    found = tracker.find_marker(marker)
    
    if found:
        print('Distance (in cm): ', tracker.distance_to_marker)
        print('Angle: ', tracker.angle_to_marker)
    else:
        logger.error(f"Didn't find marker {marker}")
    sleep(0.5)

from threading import Thread
import configparser
import os
from time import sleep

from libs import UDPOut
from libs import Location
from libs import ARTracker

class Drive:
    
    def __init__(self, baseSpeed, cameras):
        self.baseSpeed = baseSpeed
        self.tracker = ARTracker.ARTracker(cameras)
        
        #sets up the parser
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(os.path.dirname(__file__) + '/../config.ini')
        
        #parses config
        self.mbedIP = str(config['CONFIG']['MBED_IP'])
        self.mbedPort = int(config['CONFIG']['MBED_PORT'])
        swiftIP = str(config['CONFIG']['SWIFT_IP'])
        swiftPort = str(config['CONFIG']['SWIFT_PORT'])
        self.gps = Location.Location(swiftIP, swiftPort)
        self.gps.start_GPS()
        
        self.rightSpeed = 0.0
        self.leftSpeed = 0.0
        self.errorAccumulation = 0.0
        
        #starts the thread that sends wheel speeds
        self.running = True
        t = Thread(target=self.sendSpeed, name=('send wheel speeds'), args=())
        t.daemon = True
        t.start()
    
    #Every 100ms, send the current left and right wheel speeds to the mbeds
    def sendSpeed(self):
        while self.running:
            ls = int(self.leftSpeed) + 90 #TODO: verify we want to send values 0-180 instead of -90 to 90
            rs = int(self.rightSpeed) + 90
            UDPOut.sendWheelSpeeds(self.mbedIP, self.mbedPort, ls,ls,ls, rs,rs,rs)
            sleep(.1)
    
    #time in milliseconds
    #error in degrees
    #Gets adjusted speeds based off of error and how long its been off (uses p and i)   
    def getSpeeds(self,speed, error, time):
        values = [0,0]

        #p and i constants if not doing a pivot turn
        kp = .3
        ki = .000001

        #p and i constants if doing a pivot turn
        if speed == 0:
            kp = .7
            ki = .0004

        #Updates the error accumulation
        self.errorAccumulation += error * time

        #Gets the adjusted speed values
        values[0] = speed - (error * kp + self.errorAccumulation * ki)
        values[1] = speed + (error * kp - self.errorAccumulation * ki)

        #Gets the maximum speed values depending if it is pivoting or not
        min = speed  - 30
        max = speed + 30
        if speed == 0:
            max += 30
            min -= 30
        if max > 90:
            max=90
        if min < -90:
            min = -90
            
        #Makes sure the adjusted speed values are within the max and mins
        if values[0] > max:
            values[0] = max
        elif values[0] < min:
            values[0] = min
        if values[1] > max:
            values[1] = max
        elif values[1] < min:
            values[1] = min
       
        #Makes sure the speeds are >10 or <-10. Wheels lock up if the speeds are <10 and >-10
        if values[0] <= 0 and values[0] > -10:
            values[0] = -10
        elif values[0] > 0 and values[0] < 10:
            values[0] = 10
        
        if values[1] <= 0 and values[1] > -10:
            values[1] = -10
        elif values[1] > 0 and values[1] < 10:
            values[1] = 10
            
        return values
        
    #Cleaner way to print out the wheel speeds
    def printSpeeds(self):
        print("Left wheels: ", round(self.leftSpeed,1))
        print("Right wheels: ", round(self.rightSpeed,1))
    
    #Drives along a given list of GPS coordinates while looking for the given ar markers
    #Keep id2 at -1 if looking for one post, set id1 to -1 if you aren't looking for AR markers 
    def driveAlongCoordinates(self, locations, id1, id2=-1):
        #Starts the GPS
        self.gps.start_GPS_thread()
        print('Waiting for GPS connection...')
        #while self.gps.all_zero: 
        #    continue
        print('Connected to GPS')
        
        #backs up and turns to avoid running into the last detected sign. Also allows it to get a lock on heading
        self.leftSpeed = -60
        self.rightSpeed = -60
        sleep(2)
        self.leftSpeed = 0
        self.rightspeed = 0
        sleep(2)
        self.leftSpeed = 80
        self.rightSpeed = 20
        sleep(4)
        
        #navigates to each location
        for l in locations:
            self.errorAccumulation = 0
            while self.gps.distance_to(l[0], l[1]) > .002: #.002km
                bearingTo = self.gps.bearing_to(l[0], l[1])
                speeds = self.getSpeeds(self.baseSpeed, bearingTo, 100) #It will sleep for 100ms
                self.leftSpeed = speeds[1]
                self.rightSpeed = speeds[0]
                sleep(.1) #Sleeps for 100ms
                self.printSpeeds()
                
                if(id1 != -1 and self.tracker.findMarker(id1, id2)):
                    self.gps.stop_GPS_thread()
                    print('Found Marker!')
                    self.leftSpeed = 0
                    self.rightSpeed = 0
                    return True
                    
        self.gps.stop_GPS_thread()
        print('Made it to location without seeing marker(s)')
        self.leftSpeed = 0
        self.rightSpeed = 0
        return False
                
    def trackARMarker(self, id1, id2=-1):
        stopDistance = 20 #stops when 250cm from markers TODO make sure rover doesn't stop too far away with huddlys
        timesNotFound = -1
        self.tracker.findMarker(id1, id2) #Gets and initial angle from the main camera
        self.errorAccumulation = 0
        
        if id2 == -1:
            #Centers the middle camera with the tag
            while self.tracker.angleToMarker > 20 or self.tracker.angleToMarker < -18:
                if self.tracker.findMarker(id1, cameras=1): #Only looking with the center camera right now
                    speeds = self.getSpeeds(0, self.tracker.angleToMarker, 100)
                    self.leftSpeed = speeds[1]
                    self.rightSpeed = speeds[0]
                    print(self.tracker.angleToMarker, " ", self.tracker.distanceToMarker)
                    timesNotFound = 0
                elif timesNotFound == -1: #Never seen the tag with the main camera
                    self.leftSpeed = 10
                    self.rightSpeed = 80
                elif timesNotFound < 15: #Lost the tag for less than a second after seeing it with the main camera
                    timesNotFound += 1
                    print(f"lost tag {timesNotFound} times")
                else:
                    self.leftSpeed = 0
                    self.rightSpeed = 0
                    print("lost it") #TODO this is bad
                    return False
                self.printSpeeds()
                sleep(.1)
            
            self.leftSpeed = 0
            self.rightSpeed = 0
            sleep(.5)
            self.errorAccumulation = 0
            print("Locked on and ready to track")
            
            #Tracks down the tag
            while self.tracker.distanceToMarker > stopDistance or self.tracker.distanceToMarker == -1: #-1 means we lost the tag
                markerFound = self.tracker.findMarker(id1, cameras = 1) #Looks for the tag
                
                if self.tracker.distanceToMarker > stopDistance:
                    speeds = self.getSpeeds(self.baseSpeed, self.tracker.angleToMarker, 100)
                    self.leftSpeed = speeds[1]
                    self.rightSpeed = speeds[0]
                    timesNotFound = 0
                    print(f"Tag is {self.tracker.distanceToMarker}cm away at {self.tracker.angleToMarker} degrees")
                    
                elif self.tracker.distanceToMarker == -1 and timesNotFound < 15:
                    timesNotFound += 1
                    print(f"lost tag {timesNotFound} times")
                    
                elif self.tracker.distanceToMarker == -1:
                    self.leftSpeed = 0
                    self.rightSpeed = 0
                    print("Lost tag")
                    return False #TODO this is bad
                
                self.printSpeeds()
                sleep(.1)
            
            #We scored!
            self.leftSpeed = 0
            self.rightSpeed = 0
            return True
        else:
            #Look for the center of the posts
            #Get the angle and the distance from the rover
            #backup a few seconds and then drive forward the same distance and save the calculated bearing from that
            #Create a new method in location that returns the lat/lon given an angle and a distance
            #drive to the lat/lon taken from the previous line
            pass
        
                        
        
         
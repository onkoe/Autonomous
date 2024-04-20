from threading import Thread
from threading import Timer
import configparser
import os
from typing import Tuple
import math
from time import sleep
import sys

# FIXME(bray): we should be building rovermap into a package. that'd make importing easier
sys.path.append("../../Mission Control/RoverMap/")  # TODO: PLEASE FIX ME
from server import MapServer

from libs import UDPOut
from libs import Location
from libs import ARTracker


class Drive:
    def __init__(self, base_speed, cameras):
        self.base_speed = base_speed
        self.tracker = ARTracker.ARTracker(cameras)

        # Starts everything needed by the map
        self.map_server = MapServer()
        self.map_server.register_routes()
        self.map_server.start(debug=False)
        self.start_map(self.update_map, 0.5)
        sleep(0.1)

        # sets up the parser
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(os.path.dirname(__file__) + "/../config.ini")

        # parses config
        self.mbed_IP = str(config["CONFIG"]["MBED_IP"])
        self.mbed_port = int(config["CONFIG"]["MBED_PORT"])
        swift_IP = str(config["CONFIG"]["SWIFT_IP"])
        swift_port = str(config["CONFIG"]["SWIFT_PORT"])
        self.gps = Location.Location(swift_IP, swift_port)
        self.gps.start_GPS()

        self.speeds = [0, 0]
        self.error_accumulation = 0.0

        # starts the thread that sends wheel speeds
        self.running = True
        t = Thread(target=self.send_speed, name=("send wheel speeds"), args=())
        t.daemon = True
        t.start()

    # startMap
    def start_map(self, func, seconds):
        def func_wrapper():
            self.start_map(func, seconds)
            func()

        t = Timer(seconds, func_wrapper)
        t.start()
        return t

    # updateMap
    def update_map(self):
        self.map_server.update_rover_coords([self.gps.latitude, self.gps.longitude])

    # Every 100ms, send the current left and right wheel speeds to the mbeds
    # sendSpeed
    def send_speed(self):
        while self.running:
            # left and right speed
            ls = int(self.speeds[0])
            rs = int(self.speeds[1])
            UDPOut.send_wheel_speeds(
                self.mbed_IP, self.mbed_port, ls, ls, ls, rs, rs, rs
            )
            sleep(0.1)

    # TODO: use the `pid_controller` library instead
    def get_speeds(self, base_speed, error, time, kp=0.35, ki=0.000035):
        """! Gets the adjusted wheel speed values using a PID controller

        @param speed The base speed for the rover
        @param error The current bearing to the designated coordinate
        @param time  Miliseconds
        @param kp    P value
        @param ki    I value
        """
        print("Current bearing to objective:", error)

        # values -> speed_values
        speed_values = [0, 0]  # [Left wheel speeds, right wheel speeds]
        min_wheel_speed = -90  # Minimum accepted speed value
        max_wheel_speed = 90  # Maximum accepted speed value

        # Updates the error accumulation
        self.error_accumulation += error * time

        # Gets the adjusted speed values
        speed_values[0] = base_speed + (error * kp)  # + self.error_accumulation * ki)
        speed_values[1] = base_speed - (error * kp)  # + self.error_accumulation * ki)

        # Makes sure the adjusted speed values are within min and max wheel speed values
        speed_values[0] = min(speed_values[0], max_wheel_speed)
        speed_values[0] = max(speed_values[0], min_wheel_speed)

        speed_values[1] = min(speed_values[1], max_wheel_speed)
        speed_values[1] = max(speed_values[1], min_wheel_speed)

        # Make sure the wheels aren't in deadlock
        # Because if they're between -10 and 10 the rover won't move
        if speed_values[0] < 0 and speed_values[0] > -10:
            speed_values[0] = -30
        elif speed_values[0] > 0 and speed_values[0] < 10:
            speed_values[0] = 30

        if speed_values[1] < 0 and speed_values[1] > -10:
            speed_values[1] = -30
        elif speed_values[1] > 0 and speed_values[1] < 10:
            speed_values[1] = 30

        return speed_values

    # Cleaner way to print out the wheel speeds
    # printSpeeds
    def print_speeds(self):
        print("Left wheels: ", round(self.speeds[0], 1))
        print("Right wheels: ", round(self.speeds[1], 1))

    # Drives along a given list of GPS coordinates while looking for the given ar markers
    # Keep aruco_id2 at -1 if looking for one post, set aruco_id1 to -1 if you aren't looking for AR markers
    # driveAlongCoordinates
    def drive_along_coordinates(
        self, locations: list[Tuple[float, float]], aruco_id1: int, aruco_id2: int = -1
    ) -> bool:
        # Starts the GPS
        self.gps.start_GPS_thread()
        print("Waiting for GPS connection...")
        # while self.gps.all_zero:
        #    continue
        print("Connected to GPS")

        # backs up and turns to avoid running into the last detected sign. Also allows it to get a lock on heading
        if aruco_id1 > -1:
            self.speeds = [-60, -60]
            self.print_speeds()
            sleep(2)
            self.speeds = [0, 0]
            self.print_speeds()
            sleep(2)
            self.speeds = [80, 20]
            self.print_speeds()
            sleep(4)
        else:
            self.speeds = (self.base_speed, self.base_speed)
            self.print_speeds()
            sleep(3)

        # navigates to each location
        for lat, long in locations:
            self.error_accumulation = 0

            while self.gps.distance_to(lat, long) > 0.0025:  # .0025km
                bearing_to = self.gps.bearing_to(lat, long)
                print(self.gps.distance_to(lat, long))
                self.speeds = self.get_speeds(
                    # change self.base_speed to base_speed
                    self.base_speed,
                    bearing_to,
                    200,
                )  # It will sleep for 100ms
                sleep(0.2)  # Sleeps for 100ms
                self.print_speeds()

                if aruco_id1 != -1 and self.tracker.find_marker(aruco_id1, aruco_id2):
                    self.gps.stop_GPS_thread()
                    print("Found Marker!")
                    self.speeds = [0, 0]
                    return True

        self.gps.stop_GPS_thread()
        print("Made it to location without seeing marker(s)")
        self.speeds = [0, 0]
        return False

    def track_AR_Marker(self, aruco_id1: int, aruco_id2: int = -1):
        stop_distance = 350  # stops when 250cm from markers TODO make sure rover doesn't stop too far away with huddlys
        times_not_found = -1
        self.tracker.find_marker(
            aruco_id1, aruco_id2, cameras=1
        )  # Gets and initial angle from the main camera
        self.error_accumulation = 0

        count = 0
        # Centers the middle camera with the tag
        while self.tracker.angle_to_marker > 14 or self.tracker.angle_to_marker < -14:
            if self.tracker.find_marker(
                aruco_id1, aruco_id2, cameras=1
            ):  # Only looking with the center camera right now
                if times_not_found == -1:
                    self.speeds = [0, 0]
                    sleep(0.5)
                    self.speeds = [self.base_speed, self.base_speed]
                    sleep(0.8)
                    self.speeds = [0, 0]
                else:
                    self.speeds = self.get_speeds(0, self.tracker.angle_to_marker, 100)
                print(
                    self.tracker.angle_to_marker, " ", self.tracker.distance_to_marker
                )
                times_not_found = 0
            elif times_not_found == -1:  # Never seen the tag with the main camera
                if math.ceil(int(count / 20) / 5) % 2 == 1:
                    self.speeds = [self.base_speed + 5, -self.base_speed - 5]
                else:
                    self.speeds = [-self.base_speed - 5, self.base_speed + 5]
            elif (
                times_not_found < 15
            ):  # Lost the tag for less than 1.5 seconds after seeing it with the main camera
                times_not_found += 1
                print(f"lost tag {times_not_found} times")
            else:
                self.speeds = [0, 0]
                print("lost it")  # TODO this is bad
                times_not_found = -1
                # return False
            self.print_speeds()
            sleep(0.1)
            count += 1
        self.speeds = [0, 0]
        sleep(0.5)

        self.error_accumulation = 0
        print("Locked on and ready to track")

        # Tracks down the tag
        while (
            self.tracker.distance_to_marker > stop_distance
            or self.tracker.distance_to_marker == -1
        ):  # -1 means we lost the tag
            self.tracker.marker_found = self.tracker.find_marker(
                aruco_id1, cameras=1
            )  # Looks for the tag

            if self.tracker.distance_to_marker > stop_distance:
                self.speeds = self.get_speeds(
                    self.base_speed - 8,
                    self.tracker.angle_to_marker,
                    100,
                    kp=0.5,
                    ki=0.0001,
                )
                times_not_found = 0
                print(
                    f"Tag is {self.tracker.distance_to_marker}cm away at {self.tracker.angle_to_marker} degrees"
                )

            elif self.tracker.distance_to_marker == -1 and times_not_found < 10:
                times_not_found += 1
                print(f"lost tag {times_not_found} times")

            elif self.tracker.distance_to_marker == -1:
                self.speeds = [0, 0]
                print("Lost tag")
                return False  # TODO this is bad

            self.print_speeds()
            sleep(0.1)

        # We scored!
        self.speeds = [0, 0]
        print("In range of the tag!")
        return True

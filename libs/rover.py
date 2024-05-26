import configparser
import os
from dataclasses import dataclass
from threading import Thread
from time import sleep

import cv2

from libs import config
from libs.communication import Communication
from libs.navigation import Navigation
from maps.server import MapServer


@dataclass
class Mode:
    SEARCHING_ALONG_COORDINATE = 0
    ARUCO = 1
    YOLO = 2

    state: int


@dataclass()
class Rover:
    """
    A representation of the rover.
    """

    conf: config.Config
    rover_connection: Communication
    opencv_camera_index: int
    nav: Navigation
    mode: Mode

    def __init__(self, given_coords: Coordinate, opencv_camera_index: int):
        # sets up the parser
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(os.path.dirname(__file__) + "/../config.ini")

        # initialize the gps object
        # this starts a thread for the gps
        self.nav = Navigation(
            config,
            given_coords,
            swift_ip=self.conf.gps_ip(),
            swift_port=self.conf.gps_port(),
        )
        self.gps.start_GPS()

        self.speeds = [0, 0]
        self.error_accumulation = 0.0

        # TODO: Initiate different threads
        # ✅ Navigation thread
        # - Communication thread
        # - Aruco Tracker/YOLO thread
        # - RoverMap Thread

        self.opencv_camera_index = opencv_camera_index
        self.rover_connection = Communication(self.conf.gps_ip(), self.conf.gps_port())

        pass

    def start_navigation_thread(self):
        # What does navigati
        pass

    def start_communication_thread(self):
        # starts the thread that sends wheel speeds
        self.running = True
        t = Thread(target=self.send_speed, name=("send wheel speeds"), args=())
        t.daemon = True
        t.start()
        pass

    def start_aruco_tracker_thread(self):
        pass

    def start_yolo_thread(self):
        pass

    def start_rover_map(self):
        # Starts everything needed by the map
        self.map_server = MapServer()
        self.map_server.register_routes()
        self.map_server.start(debug=False)
        self.start_map(self.update_map, 0.5)
        sleep(0.1)
        pass

    def pid_controller(self):
        """
        Read from navigation thread and send commands through communication thread
        """
        pass


@dataclass()
class Yolo:
    """
    Captures frames and checks for competition objects in a frame. Computes bounding boxes.
    """

    aruco_marker: int
    video_capture: cv2.VideoCapture

    def __init__(self):
        """
        Initialize YOLO detection model
        """

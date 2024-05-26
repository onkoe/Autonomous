from dataclasses import dataclass
from multiprocessing import Process, Queue
from time import sleep

import cv2
from loguru import logger

from libs.config import Config
from libs.args import Args
from libs.aruco_tracker import ArucoTracker
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
    arguments: Args
    conf: Config
    mode: Mode
    
    rover_connection: Communication
    communication_queue: Queue
    communication_process: Process
    
    nav: Navigation
    navigation_queue: Queue
    
    aruco_tracker: ArucoTracker
    aruco_tracker_queue: Queue

    def __init__(self):
        # get arguments
        logger.info("Parsing arguments...")
        self.arguments = Args()
        
        self.mode = Mode.SEARCHING_ALONG_COORDINATE
        
        # check arguments for aruco id. set self.mode accordingly
        if self.arguments.aruco_id is None:
            logger.info("No ArUco markers were given. Let's navigate to the given coordinates.")
            self.mode = self.mode
            # go to coordinate
            
        else:
            self.mode = Mode.SEARCHING_ALONG_COORDINATE
            # go to coordinate
            # TODO: when that's done, look for the marker
        logger.info("Parsed arguments successfully!")
        
        # sets up the parser
        self.conf = Config("../config.ini")
        

        self.speeds = [0, 0]
        self.error_accumulation = 0.0

        # TODO: Initiate different threads
        # ✅ Navigation thread
        # - Communication thread
        # - Aruco Tracker/YOLO thread
        # - RoverMap Thread

        self.rover_connection = Communication(self.conf.gps_ip(), self.conf.gps_port())

        pass

    def start_navigation(self):
        # initialize the gps object
        # this starts a thread for the gps, as this module handles that itself
        self.nav = Navigation(
            self.conf,
            self.arguments.coordinate_list, # FIXME: needs to take a list??? or manage it manual
        )
        
        pass

    def start_communication(self):
        # starts the thread that sends wheel speeds
        proc = Process(target=self.rover_connection.handle_commands, name="send wheel speeds") # FIXME
        proc.daemon = True # FIXME: don't do this
        proc.start()
        
        logger.info("Started the communication thread!")
        self.communication_process = proc
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

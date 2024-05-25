from dataclasses import dataclass
from threading import Thread
from time import sleep

from loguru import logger
from geographiclib.geodesic import Geodesic

from gps import gps
from libs import config
from libs.navigation import Coordinate


@dataclass()
class GpsController:
    """
    Controls the GPS library.
    """

    conf: config.Config
    enabled: bool = False  # whether or not gps comms are enabled

    # note: if you change these, make sure to go to GpsReport too
    coordinates: Coordinate = Coordinate(0.0, 0.0)
    height: float = 0.0  # in meters
    time: float = 0.0  # "time of week" in milliseconds
    error: float = 0.0  # in millimeters, accounting for vert/horiz error
    true_bearing: float = 0.0  # Bearing from True North
    previous_coordinates: Coordinate = Coordinate(0.0, 0.0)

    SLEEP_TIME: float = 0.1

    def __init__(self, swift_ip: str, swift_port: int):
        """
        Initialize Location object to get coordinates
        """
        pass

    def start(self):
        """
        Starts the GPS thread and connects to the GPS hardware itself.
        """
        gps.gps_init(self.conf.gps_ip(), self.conf.gps_port())
        self.enabled = True

        logger.info("Starting GPS thread...")
        t = Thread(target=self.check, name=("GPS thread"), args=())
        t.start()
        logger.info("GPS thread started!")
        pass

    def stop(self):
        """
        Sets the GPS state to be off, causing the GPS thread to stop.
        """
        self.enabled = False
        gps.gps_finish()

    def check(self):
        while self.enabled:
            if gps.get_latitude() + gps.get_longitude() == 0:
                logger.error("Expected GPS data but got none.")
            else:
                # we've got GPS data. let's do our thing...
                # make current coords old
                self.previous_coordinates = self.coordinates

                # get new values
                self.coordinates = Coordinate(gps.get_latitude(), gps.get_longitude())
                self.height = gps.get_height()
                self.time = gps.get_time()
                self.error = gps.get_error()

                # calculate true bearing between new and old coordinates
                self.true_bearing = calculate_true_bearing(
                    self.previous_coordinates, self.coordinates
                )

                # TODO: make report and send to navigation thread

            sleep(self.SLEEP_TIME)

        logger.info("GPS thread: no longer enabled, shutting down...")


def calculate_true_bearing(prev_coords: Coordinate, curr_coords: Coordinate) -> float:
    """
    Calculate the True Bearing for an object given its current position and previous position.
    NOTE: True bearing is the bearing relative to North

    - `co1`: first coordinate.
    - `co2`: second coordinate.
    """
    earth = Geodesic.WGS84

    res = earth.Inverse(
        prev_coords.get_latitude(),
        prev_coords.get_longitude(),
        curr_coords.get_latitude(),
        curr_coords.get_longitude(),
    )
    true_bearing: float = res["azi1"]

    logger.debug(f"True bearing: `{true_bearing}`°")
    return true_bearing


@dataclass()
class GpsReport:
    """
    A container for GPS data. Sendable across threads.
    """

    # important: ensure you keep these fields matched with GpsController
    current_coordinates: Coordinate = Coordinate(0.0, 0.0)
    height: float = 0.0  # in meters
    time: float = 0.0  # "time of week" in milliseconds
    error: float = 0.0  # in millimeters, accounting for vert/horiz error
    true_bearing: float = 0.0  # in degrees
    previous_coordinates: Coordinate = Coordinate(0.0, 0.0)

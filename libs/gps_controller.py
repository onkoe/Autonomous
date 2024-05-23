from dataclasses import dataclass
from threading import Thread
from time import sleep

from loguru import logger

from gps import gps
from libs import config, navigation
from libs.navigation import Coordinate


@dataclass(kw_only=True)
class GpsController:
    """
    Controls the GPS library.
    """

    enabled: bool = False  # whether or not gps comms are enabled
    config: config.Config

    coordinates: Coordinate = Coordinate(0.0, 0.0)
    height: float = 0.0  # in meters
    time: float = 0.0  # "time of week" in milliseconds
    error: float = 0.0  # in millimeters, accounting for vert/horiz error
    angle: float = 0.0  # in degrees
    previous_coordinates: Coordinate = Coordinate(0.0, 0.0)

    SLEEP_TIME: float = 0.1

    def __init__(self, swift_ip: int, swift_port: int):
        """
        Initialize Location object to get coordinates
        """
        pass

    def start(self):
        """
        Starts the GPS thread and connects to the GPS hardware itself.
        """
        gps.gps_init(self.config.swift_ip(), self.config.swift_port())
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

                # calculate angle ("bearing") between new and old coordinates
                self.angle = navigation.calculate_angle(
                    self.coordinates, self.previous_coordinates
                )

            sleep(self.SLEEP_TIME)

        logger.info("GPS thread: no longer enabled, shutting down...")

from dataclasses import dataclass
from typing import Union

from geographiclib.geodesic import Geodesic
from loguru import logger

from libs import rover
from libs.config import Config
from libs.gps_controller import GpsController
from gps_controller import calculate_true_bearing


@dataclass()
class Coordinate:
    latitude: float
    longitude: float

    def get_latitude(self) -> float:
        self.latitude

    def get_longitude(self) -> float:
        self.longitude

    def set_latitude(self, latitude: float):
        self.latitude = latitude

    def set_longitude(self, longitude: float):
        self.longitude = longitude

    def __str__(self):
        return f"({self.latitude}, {self.longitude})"


@dataclass()
class Navigation:
    """
    Keeps track of latititude and longitude of objective, distance to objective, and angle to objective.

    It also calculates some of these values.

    The rover should run the `finish` method when it is done navigating.

    - `given_coords`: a given gps coordinate to navigate to. Depending on
        section of comp, ARUCO tags will be nearby
    """

    config: Config
    given_coords: Coordinate
    gps: Union[GpsController, None] = None

    def __init__(
        self, config: Config, given_coords: Coordinate, swift_ip: str, swift_port: int
    ):
        """
        Initializes the navigation to get coordinates.
        """
        self.given_coords = given_coords
        self.config = config
        self.gps = GpsController(swift_ip, swift_port)
        self.gps.start()

    def finish(self):
        """
        Stops the GPS thread and shuts down the GPS controller.

        This should always be called when the rover finishes navigation.
        """
        if self.gps is not None:
            self.gps.stop()
            self.gps = None

    def distance_to_object(self, coord: Coordinate) -> float:
        """
        Finds the distance between the rover and `coord`.
        """
        if self.gps is None:
            logger.error("GPS should be initialized before finding distance.")
            return 0.0
        else:
            rover_coords = self.gps.coordinates
            earth: Geodesic = Geodesic.WGS84
            res = earth.Inverse(
                rover_coords.get_latitude(),
                rover_coords.get_longitude(),
                coord.get_latitude(),
                coord.get_longitude(),
            )
            distance: float = res["s12"]

        logger.debug(f"Distance between `{rover_coords}` and `{coord}`: `{distance}`m")
        return distance

    def angle_to_object(self, coord: Coordinate) -> float:
        """
        Finds the angle between the rover and `coord`.
        """

        # Get all the cool stuff to calculate bearing from rover to coordinate
        rover_coords = self.gps.coordinates
        rover_true_bearing = self.gps.true_bearing
        true_bearing_to_coordinate = calculate_true_bearing(rover_coords, coord)

        # The relative bearing to an coordinate is the difference between
        # the true bearing of the coordinate and the true bearing of the rover
        relative_bearing = true_bearing_to_coordinate - rover_true_bearing

        # Ensure relative bearing is > -180 and < 180
        if relative_bearing < -180:  # Bearing is < 180 so add 360
            return relative_bearing + 360
        elif relative_bearing > 180:  # Bearing is > 180 so subtract 360
            return relative_bearing - 360
        return relative_bearing  # The bearing is just right :3

    def coordinates_to_object(self, distance_km: float, angle_deg: float) -> Coordinate:
        """
        Calculates the coordinates of another object compared to the Rover.

        - `distance_km`: The object's distance from the Rover in kilometers.
        - `angle_deg`: The object's angle from the Rover in degrees.
        """
        rover_coords = self.__get_gps_coordinates()

        earth: Geodesic = Geodesic.WGS84
        res = earth.Direct(
            distance_km,
            angle_deg,
            rover_coords.get_latitude(),
            rover_coords.get_longitude(),
        )
        c = Coordinate(res["lat2"], res["lon2"])

        logger.debug(f"Object coordinates (lat, lon): {c}")
        return c

    def __get_gps_coordinates(self) -> Coordinate:
        if self.gps is None:
            logger.error("GPS was expected to be initialized, but it wasn't!")
            return Coordinate(0.0, 0.0)
        else:
            return self.gps.coordinates


def calculate_angle(self, co1: Coordinate, co2: Coordinate) -> float:
    """
    Calculates the angle between two coordinates.
    The angle between the direction of the rover and North

    - `co1`: first coordinate.
    - `co2`: second coordinate.
    """
    earth: Geodesic = Geodesic.WGS84
    res = earth.Inverse(
        co1.get_latitude(), co1.get_longitude(), co2.get_latitude(), co2.get_longitude()
    )
    angle: float = res["azi1"]

    logger.debug(f"Angle between `{co1}` and `{co2}`: `{angle}`°")
    return angle

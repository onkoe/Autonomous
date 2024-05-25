from dataclasses import dataclass

from geographiclib.geodesic import Geodesic
from loguru import logger

from libs.config import Config
from libs.gps_controller import GpsController


@dataclass()
class Coordinate:
    latitude: float
    longitude: float

    def latitude(self) -> float:
        self.latitude

    def longitude(self) -> float:
        self.longitude

    def set_latitude(self, latitude: float):
        self.latitude = latitude

    def set_longitude(self, longitude: float):
        self.longitude = longitude

    def __str__(self):
        return f"({self.latitude}, {self.longitude})"


@dataclass(kw_only=True)
class Navigation:
    """
    Keeps track of latititude and longitude, distance to objective, and angle to objective.

    It also calculates some of these values.
    
    The rover should run the `finish` method when it is done navigating.

    - `given_coords`: a given gps coordinate to navigate to. Depending on
        section of comp, ARUCO tags will be nearby
    """

    config: Config
    given_coords: Coordinate
    gps: GpsController | None = None

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
        self.gps.stop()
        self.gps = None
    
    def distance_to_object(self, coord: Coordinate) -> float:
        """
        Finds the distance between the rover and `coord`.
        """
        earth: Geodesic = Geodesic.WGS84
        res = earth.Inverse(
            self.rover_coords.latitude(),
            self.rover_coords.longitude(),
            coord.latitude(),
            coord.longitude(),
        )
        distance: float = res["s12"]

        logger.debug(
            f"Distance between `{self.rover_coords}` and `{coord}`: `{distance}`m"
        )
        return distance

    def angle_to_object(self, coord: Coordinate) -> float:
        """
        Finds the angle between the rover and `coord`.
        """
        return calculate_angle(self.rover_coords, coord)

    def coordinates_to_object(self, distance_km: float, angle_deg: float) -> Coordinate:
        """
        Calculates the coordinates of another object compared to the Rover.

        - `distance_km`: The object's distance from the Rover in kilometers.
        - `angle_deg`: The object's angle from the Rover in degrees.
        """
        earth: Geodesic = Geodesic.WGS84
        res = earth.Direct(
            distance_km,
            angle_deg,
            self.rover_coords.latitude(),
            self.rover_coords.longitude(),
        )
        c = Coordinate(res["lat2"], res["lon2"])

        logger.debug(f"Object coordinates (lat, lon): {c}")
        return c


def calculate_angle(self, co1: Coordinate, co2: Coordinate) -> float:
    """
    Calculates the angle between two coordinates.

    - `co1`: first coordinate.
    - `co2`: second coordinate.
    """
    earth: Geodesic = Geodesic.WGS84
    res = earth.Inverse(
        co1.latitude(), co1.longitude(), co2.latitude(), co2.longitude()
    )
    angle: float = res["azi1"]

    logger.debug(f"Angle between `{co1}` and `{co2}`: `{angle}`°")
    return angle
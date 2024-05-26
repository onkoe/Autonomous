from dataclasses import dataclass

@dataclass
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
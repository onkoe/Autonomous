from configparser import ConfigParser

from dataclasses import dataclass

@dataclass(kw_only=True)
class Config:
    """
    A container for the rover's configuration.
    """
    config: ConfigParser
    
    ##### MBED, for controlling the LEDs #####
    
    def mbed_ip(self) -> str:
        """
        Returns the IP address of the MBED micro-controller.
        """
        return str(self.config["CONFIG"]["MBED_IP"])
    
    def mbed_port(self) -> int:
        """
        Returns the port number of the MBED micro-controller.
        """
        return int(self.config["CONFIG"]["MBED_PORT"])
    
    ##### Swift, for getting GPS coordinates #####
    
    def gps_ip(self) -> str:
        """
        Returns the IP address of the Swift GPS module.
        """
        return str(self.config["CONFIG"]["SWIFT_IP"])
    
    def gps_port(self) -> int:
        """
        Returns the port number of the Swift GPS module.
        """
        return int(self.config["CONFIG"]["SWIFT_PORT"])
    
    ##### OpenCV format #####
    
    def opencv_format(self) -> str:
        """
        Returns the OpenCV format string for camera initialization.
        """
        return self.config["ARTRACKER"]["FORMAT"]
    
    ##### Camera traits, for object distances and angles #####
    
    def camera_hdegrees_per_pixel(self) -> float:
        """
        Returns the horizontal degrees per pixel for the camera.
        """
        return float(self.config["ARTRACKER"]["DEGREES_PER_PIXEL"])

    def camera_vdegrees_per_pixel(self) -> float:
        """
        Returns the vertical degrees per pixel for the camera.
        """
        return float(self.config["ARTRACKER"]["VDEGREES_PER_PIXEL"])
    
    def camera_frame_width(self) -> int:
        """
        Returns the width of the camera frame.
        """
        return int(self.config["ARTRACKER"]["FRAME_WIDTH"])

    def camera_frame_height(self) -> int:
        """
        Returns the height of the camera frame.
        """
        return int(self.config["ARTRACKER"]["FRAME_HEIGHT"])
    
    def camera_focal_length(self) -> float:
        """
        The focal length of the camera.
        """
        return float(self.config["ARTRACKER"]["FOCAL_LENGTH"])
    
    ## TODO: remove these if we use the OpenCV distance/angle function
    
    def camera_known_marker_size(self) -> float:
        """
        The real-world width/height of an ARUCO marker. This helps calculate 
        the distance/angle to the marker.
        """
        return float(self.config["ARTRACKER"]["KNOWN_TAG_WIDTH"])

    def camera_focal_length30h(self) -> float:
        """
        The focal length of the camera at 30 degrees horizontal.
        """
        return float(self.config["ARTRACKER"]["FOCAL_LENGTH30H"])

    def camera_focal_length30v(self) -> float:
        """
        The focal length of the camera at 30 degrees vertical.
        """
        return float(self.config["ARTRACKER"]["FOCAL_LENGTH30V"])
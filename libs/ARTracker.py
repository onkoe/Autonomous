import cv2
import cv2.aruco as aruco
import configparser
import os
from typing import List

from loguru import logger

# TODO(bray): `dataclasses`
class ARTracker:
    # Constructor
    # Cameras should be a list of file paths to cameras that are to be used
    # set write to True to write to disk what the cameras are seeing
    # set use_YOLO to True to use yolo when attempting to detect the ar tags
    
    # TODO: Get rid of use_yolo?
    # TODO: Add type declarations
    # TODO: Can we not have our initialization function be over 80 lines?
    def __init__(self, cameras: List[int], write: bool = False, use_YOLO: bool = False, config_file: str ="config.ini") -> None:
        """
        Constructs a new ARTracker.
        
        - `cameras` is a list of OpenCV camera values.
        - `write` tells the camera to save video files.
        - `config_file` is a path to the config file (relative or absolute).
        """
        
        
        self.write = write
        self.distance_to_marker = -1
        self.angle_to_marker = -999.9
        self.index1 = -1
        self.index2 = -1
        self.use_YOLO = use_YOLO
        self.cameras = cameras

        # Open the config file
        config = configparser.ConfigParser(allow_no_value=True)
        if not config.read(config_file):
            logger.info("ERROR OPENING AR CONFIG:")
            if os.path.isabs(config_file):
                print(config_file)
            else:
                print(f"{os.getcwd()}/{config_file}")
            exit(-2)

        # Set variables from the config file
        # TODO: Could this be in a function
        self.degrees_per_pixel = float(config["ARTRACKER"]["DEGREES_PER_PIXEL"])
        self.vdegrees_per_pixel = float(config["ARTRACKER"]["VDEGREES_PER_PIXEL"])
        self.focal_length = float(config["ARTRACKER"]["FOCAL_LENGTH"])
        self.focal_length30H = float(config["ARTRACKER"]["FOCAL_LENGTH30H"])
        self.focal_length30V = float(config["ARTRACKER"]["FOCAL_LENGTH30V"])
        self.known_marker_width = float(config["ARTRACKER"]["KNOWN_TAG_WIDTH"])
        self.format = config["ARTRACKER"]["FORMAT"]
        self.frame_width = int(config["ARTRACKER"]["FRAME_WIDTH"])
        self.frame_height = int(config["ARTRACKER"]["FRAME_HEIGHT"])

        # Initialize video writer, fps is set to 5
        if self.write:
            self.video_writer = cv2.VideoWriter(
                "autonomous.avi",
                cv2.VideoWriter.fourcc(
                    self.format[0], self.format[1], self.format[2], self.format[3]
                ),
                5,
                (self.frame_width, self.frame_height),
                False,
            )

        # Set the ar marker dictionary
        self.marker_dict = aruco.DICT_4X4_50

        # Initialize cameras
        # TODO: Could this be in a function
        # TODO: Also replace with logger 
        self.caps = []
        if isinstance(self.cameras, int):
            self.cameras = [self.cameras]
        for i in range(0, len(self.cameras)):
            # Makes sure the camera actually connects
            while True:
                cam = cv2.VideoCapture(self.cameras[i])
                if not cam.isOpened():
                    logger.info(
                        f"!!!!!!!!!!!!!!!!!!!!!!!!!!Camera {i} did not open!!!!!!!!!!!!!!!!!!!!!!!!!!",
                    )
                    cam.release()
                    continue
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
                cam.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                cam.set(
                    cv2.CAP_PROP_BUFFERSIZE, 1
                )  # greatly speeds up the program but the writer is a bit wack because of this
                cam.set(
                    cv2.CAP_PROP_FOURCC,
                    cv2.VideoWriter.fourcc(
                        self.format[0], self.format[1], self.format[2], self.format[3]
                    ),
                )
                # ret, testIm =  self.caps[i].read()[0]
                if not cam.read()[0]:
                    cam.release()
                else:
                    self.caps.append(cam)
                    break

    # id1 is the main ar tag to telating to id2, since gateposts are no longrack, id2 is not relevant, image is the image to analyze
    # TODO: Get rid of anything relating to id2
    # markerFound
    def marker_found(self, id1: int, image, id2: int = -1) -> bool:
        """
        Attempts to find a marker with the given `id1` in the provided `image`.
        
        Returns true if found.
        """
        
        found = False
        
        # converts to grayscale
        cv2.cvtColor(image, cv2.COLOR_RGB2GRAY, image)

        self.index1 = -1
        self.index2 = -1
        bw = image  # will hold the black and white image
        # tries converting to b&w using different different cutoffs to find the perfect one for the current lighting
        for i in range(40, 221, 60):
            bw = cv2.threshold(image, i, 255, cv2.THRESH_BINARY)[1]
            detector = aruco.ArucoDetector(
                aruco.getPredefinedDictionary(self.marker_dict)
            )

            (self.corners, self.marker_IDs, self.rejected) = detector.detectMarkers(bw)
            if self.marker_IDs is not None:
                # single post
                self.index1 = -1
                # this just checks to make sure that it found the right marker
                for m in range(len(self.marker_IDs)):
                    if self.marker_IDs[m] == id1:
                        self.index1 = m
                        break

                if self.index1 != -1:
                    logger.info("Found the correct marker!")
                    found = True
                    if self.write:
                        self.video_writer.write(bw)  # purely for debug
                        cv2.waitKey(1)
                    break
                
        return found
    
        center_x_marker = (
            self.corners[self.index1][0][0][0]
            + self.corners[self.index1][0][1][0]
            + self.corners[self.index1][0][2][0]
            + self.corners[self.index1][0][3][0]
        ) / 4
        # takes the pixels from the marker to the center of the image and multiplies it by the degrees per pixel
        # FIXME(bray): wow yeah thanks for the comment, but why?
        self.angle_to_marker = self.degrees_per_pixel * (
            center_x_marker - self.frame_width / 2
        )
        
        """
        distanceToAR = (knownWidthOfMarker(20cm) * focalLengthOfCamera) / pixelWidthOfMarker
        focal_length = focal length at 0 degrees horizontal and 0 degrees vertical
        focal_length30H = focal length at 30 degreees horizontal and 0 degrees vertical
        focal_length30V = focal length at 30 degrees vertical and 0 degrees horizontal
        realFocalLength of camera = focal_length 
                                    + (horizontal angle to marker/30) * (focal_length30H - focal_length)
                                    + (vertical angle to marker / 30) * (focal_length30V - focal_length)
        If focal_length30H and focal_length30V both equal focal_length then realFocalLength = focal_length which is good for non huddly cameras
        Please note that the realFocalLength calculation is an approximation that could be much better if anyone wants to try to come up with something better
        """
        #hangle, vangle = horizontal, vertical angle
        hangle_to_marker = abs(self.angle_to_marker)
        center_y_marker = (
            self.corners[self.index1][0][0][1]
            + self.corners[self.index1][0][1][1]
            + self.corners[self.index1][0][2][1]
            + self.corners[self.index1][0][3][1]
        ) / 4
        vangle_to_marker = abs(
            self.vdegrees_per_pixel * (center_y_marker - self.frame_height / 2)
        )
        realFocalLength = (
            self.focal_length
            + (hangle_to_marker / 30) * (self.focal_length30H - self.focal_length)
            + (vangle_to_marker / 30) * (self.focal_length30V - self.focal_length)
        )
        width_of_marker = (
            (
                self.corners[self.index1][0][1][0]
                - self.corners[self.index1][0][0][0]
            )
            + (
                self.corners[self.index1][0][2][0]
                - self.corners[self.index1][0][3][0]
            )
        ) / 2
        self.distance_to_marker = (
            self.known_marker_width * realFocalLength
        ) / width_of_marker


    def find_marker(self, id1: int, id2: int = -1, cameras = -1) -> bool:
        """
        This method attempts to find a marker with the given ID. 
        Returns true if found.
        
        `id1` is the marker you want to look for.
        `cameras` is the number of cameras to check. -1 for all of them
        """
        
        if cameras == -1:
            cameras = len(self.caps)

        for i in range(cameras):
            ret, frame = self.caps[i].read()
            if self.marker_found(id1, frame, id2=id2):
                return True

        return False

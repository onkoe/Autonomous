from dataclasses import dataclass
from typing import Tuple, Union

import cv2
from loguru import logger


@dataclass()
class ArucoTracker:
    """
    Capture frames and detect ARUCO markers in frames
    """

    aruco_marker: int
    marker_size: int  # In centimeters
    # TODO: Find out how to get camera matrix and distance coefficients
    camera_mtx: type  # TODO
    distance_coefficients: type  # TODO
    aruco_dictionary: cv2.aruco.DICT_4X4_50
    video_capture: cv2.VideoCapture

    def __init__(self, opencv_camera_index: int):
        """
        Create and configure `VideoCapture` object from opencv camera index
        Create and initialize aruco dictionary
        """
        pass

    def find_marker(self) -> Union[None, Tuple[float, float]]:
        """
        Captures a frame and checks to see if `aruco_marker` is present.

        Either returns `None` if not found, or a tuple (a: float, b: float):
            - `a`: the distance to the marker in centimeters
            - `b`: the angle to the marker in degrees
        """

        # Capture a new frame
        ret, frame = self.video_capture.read()
        if not ret:
            logger.error("FRAME COULDNT BE CAPTURED! Camera may be busy.")
            return None

        # Convert frame to grayscale and try to find find a marker
        grayscale = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY, frame)
        for threshold_cutoff in range(
            40, 221, 60
        ):  # Check for arucos tags with different thresholds
            # Find aruco tags in image with given threshold cutoff
            bw = cv2.threshold(grayscale, threshold_cutoff, 255, cv2.THRESH_BINARY)[1]
            (tag_corners, aruco_tags, __) = cv2.aruco.detectMarkers(
                bw, self.marker_dict
            )

            # check if our tag is in the list of found aruco tags
            tag_index: Union[int, None] = None
            for tag in aruco_tags:
                if tag == self.aruco_marker:
                    logger.info(f"ArUco tag `{tag}` found!")
                    tag_index = tag
                    break

            # if so, let's estimate its pose
            if tag_index is not None:
                logger.debug("Checking tag pose...")
                rotation_vects, translation_vects = cv2.aruco.estimatePoseSingleMarkers(
                    tag_corners[tag_index],
                    self.marker_size,
                    self.camera_mtx,
                    self.distance_coefficients,
                )

                # calculations to get distance and angle to marker
                (distance_to_marker, angle_to_marker) = (0.0, 0.0)

                # TODO
                return (distance_to_marker, angle_to_marker)

        return None

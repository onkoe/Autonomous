import cv2
import cv2.aruco as aruco
import configparser
import os

"""
darknetPath = os.path.dirname(os.path.abspath(__file__)) + '/../YOLO/darknet/'
sys.path.append(darknetPath)
from darknet_images import *
from darknet import load_network
"""


class ARTracker:
    # Constructor
    # Cameras should be a list of file paths to cameras that are to be used
    # set write to True to write to disk what the cameras are seeing
    # set use_YOLO to True to use yolo when attempting to detect the ar tags
    def __init__(self, cameras, write=False, use_YOLO=False, config_file="config.ini"):
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
            print("ERROR OPENING AR CONFIG:")
            if os.path.isabs(config_file):
                print(config_file)
            else:
                print(f"{os.getcwd()}/{config_file}")
            exit(-2)

        # Set variables from the config file
        self.degrees_per_pixel = float(config["ARTRACKER"]["DEGREES_PER_PIXEL"])
        self.vdegrees_per_pixel = float(config["ARTRACKER"]["VDEGREES_PER_PIXEL"])
        self.focal_length = float(config["ARTRACKER"]["FOCAL_LENGTH"])
        self.focal_length30H = float(config["ARTRACKER"]["FOCAL_LENGTH30H"])
        self.focal_length30V = float(config["ARTRACKER"]["FOCAL_LENGTH30V"])
        self.known_marker_width = float(config["ARTRACKER"]["KNOWN_TAG_WIDTH"])
        self.format = config["ARTRACKER"]["FORMAT"]
        self.frame_width = int(config["ARTRACKER"]["FRAME_WIDTH"])
        self.frame_height = int(config["ARTRACKER"]["FRAME_HEIGHT"])

        # sets up yolo
        if use_YOLO:
            os.chdir(darknetPath)
            weights = config["YOLO"]["WEIGHTS"]
            cfg = config["YOLO"]["CFG"]
            data = config["YOLO"]["DATA"]
            self.thresh = float(config["YOLO"]["THRESHOLD"])
            self.network, self.class_names, self.class_colors = load_network(
                cfg, data, weights, 1
            )
            os.chdir(os.path.dirname(os.path.abspath(__file__)))

            self.network_width = darknet.network_width(self.network)
            self.network_height = darknet.network_height(self.network)

        # Initialize video writer, fps is set to 5
        if self.write:
            self.video_writer = cv2.VideoWriter(
                "autonomous.avi",
                cv2.VideoWriter_fourcc(
                    self.format[0], self.format[1], self.format[2], self.format[3]
                ),
                5,
                (self.frame_width, self.frame_height),
                False,
            )

        # Set the ar marker dictionary
        self.marker_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)

        # Initialize cameras
        self.caps = []
        if isinstance(self.cameras, int):
            self.cameras = [self.cameras]
        for i in range(0, len(self.cameras)):
            # Makes sure the camera actually connects
            while True:
                cam = cv2.VideoCapture(self.cameras[i])
                if not cam.isOpened():
                    print(
                        f"!!!!!!!!!!!!!!!!!!!!!!!!!!Camera ",
                        i,
                        " did not open!!!!!!!!!!!!!!!!!!!!!!!!!!",
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
                    cv2.VideoWriter_fourcc(
                        self.format[0], self.format[1], self.format[2], self.format[3]
                    ),
                )
                # ret, testIm =  self.caps[i].read()[0]:
                if not cam.read()[0]:
                    cam.release()
                else:
                    self.caps.append(cam)
                    break

    # helper method to convert YOLO detections into the aruco corners format
    # _convertToCorners
    def _convert_to_corners(self, detections, num_corners):
        corners = []
        x_coeff = self.frame_width / self.network_width
        y_coeff = self.frame_height / self.network_height
        if len(detections) < num_corners:
            print("ERROR, convert_to_corners not used correctly")
            raise ValueError
        for i in range(0, num_corners):
            tag_data = list(detections[i][2])  # Gets the x, y, width, height

            # YOLO resizes the image so this sizes it back to what we're exepcting
            tag_data[0] *= x_coeff
            tag_data[1] *= y_coeff
            tag_data[2] *= x_coeff
            tag_data[3] *= y_coeff

            # Gets the corners
            top_left = [tag_data[0] - tag_data[2] / 2, tag_data[1] - tag_data[3] / 2]
            top_right = [tag_data[0] + tag_data[2] / 2, tag_data[1] - tag_data[3] / 2]
            bottom_right = [
                tag_data[0] + tag_data[2] / 2,
                tag_data[1] + tag_data[3] / 2,
            ]
            bottom_left = [tag_data[0] - tag_data[2] / 2, tag_data[1] + tag_data[3] / 2]

            # appends the corners with the same format as aruco
            corners.append([[top_left, top_right, bottom_right, bottom_left]])

        return corners

    # id1 is the main ar tag to track, id2 is if you're looking at a gatepost, image is the image to analyze
    # markerFound
    def marker_found(self, id1, image, id2=-1):
        # converts to grayscale
        cv2.cvtColor(image, cv2.COLOR_RGB2GRAY, image)

        self.index1 = -1
        self.index2 = -1
        bw = image  # will hold the black and white image
        # tries converting to b&w using different different cutoffs to find the perfect one for the current lighting
        for i in range(40, 221, 60):
            bw = cv2.threshold(image, i, 255, cv2.THRESH_BINARY)[1]
            (self.corners, self.marker_IDs, self.rejected) = aruco.detectMarkers(
                bw, self.marker_dict
            )
            if self.marker_IDs is not None:
                print(
                    "", end=""
                )  # I have not been able to reproduce an error when I have a print statement here so I'm leaving it in
                if id2 == -1:  # single post
                    self.index1 = -1
                    # this just checks to make sure that it found the right marker
                    for m in range(len(self.marker_IDs)):
                        if self.marker_IDs[m] == id1:
                            self.index1 = m
                            break

                    if self.index1 != -1:
                        print("Found the correct marker!")
                        if self.write:
                            self.video_writer.write(bw)  # purely for debug
                            cv2.waitKey(1)
                        break

                    else:
                        print("Found a marker but was not the correct one")

                else:  # gate post
                    self.index1 = -1
                    self.index2 = -1
                    if len(self.marker_IDs) == 1:
                        print("Only found marker ", self.marker_IDs[0])
                    else:
                        for j in range(
                            len(self.marker_IDs) - 1, -1, -1
                        ):  # I trust the biggest markers the most
                            if self.marker_IDs[j][0] == id1:
                                self.index1 = j
                            elif self.marker_IDs[j][0] == id2:
                                self.index2 = j
                    if self.index1 != -1 and self.index2 != -1:
                        print("Found both markers!")
                        if self.write:
                            self.video_writer.write(bw)  # purely for debug
                            cv2.waitKey(1)
                        break

            if i == 220:  # did not find any AR markers with any b&w cutoff using aruco
                # Checks to see if yolo can find a tag
                if self.use_YOLO:
                    detections = []
                    if not self.write:
                        # this is a simpler detection function that doesn't return the image
                        detections = simple_detection(
                            image, self.network, self.class_names, self.thresh
                        )
                    else:
                        # more complex detection that returns the image to be written
                        image, detections = complex_detection(
                            image,
                            self.network,
                            self.class_names,
                            self.class_colors,
                            self.thresh,
                        )
                    # cv2.imwrite('ar.jpg', image)
                    for d in detections:
                        print(d)

                    if id2 == -1 and len(detections) > 0:
                        self.corners = self._convert_to_corners(detections, 1)
                        self.index1 = 0  # Takes the highest confidence ar tag
                        if self.write:
                            self.video_writer.write(image)  # purely for debug
                            cv2.waitKey(1)
                    elif len(detections) > 1:
                        self.corners = self._convert_to_corners(detections, 2)
                        self.index1 = 0  # takes the two highest confidence ar tags
                        self.index2 = 1
                        if self.write:
                            self.video_writer.write(image)  # purely for debug
                            cv2.waitKey(1)
                    print(self.corners)

                # Not even YOLO saw anything
                if self.index1 == -1 or (self.index2 == -1 and id2 != -1):
                    if self.write:
                        self.video_writer.write(image)
                        # cv2.imshow('window', image)
                        cv2.waitKey(1)
                    self.distance_to_marker = -1
                    self.angle_to_marker = -999
                    return False

        if id2 == -1:
            center_x_marker = (
                self.corners[self.index1][0][0][0]
                + self.corners[self.index1][0][1][0]
                + self.corners[self.index1][0][2][0]
                + self.corners[self.index1][0][3][0]
            ) / 4
            # takes the pixels from the marker to the center of the image and multiplies it by the degrees per pixel
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

        else:
            center_x_marker1 = (
                self.corners[self.index1][0][0][0]
                + self.corners[self.index1][0][1][0]
                + self.corners[self.index1][0][2][0]
                + self.corners[self.index1][0][3][0]
            ) / 4
            center_x_marker2 = (
                self.corners[self.index2][0][0][0]
                + self.corners[self.index2][0][1][0]
                + self.corners[self.index2][0][2][0]
                + self.corners[self.index2][0][3][0]
            ) / 4
            self.angle_to_marker = self.degrees_per_pixel * (
                (center_x_marker1 + center_x_marker2) / 2 - self.frame_width / 2
            )

            hangle_to_marker1 = abs(
                self.vdegrees_per_pixel * (center_x_marker1 - self.frame_width / 2)
            )
            hangle_to_marker2 = abs(
                self.vdegrees_per_pixel * (center_x_marker2 - self.frame_width / 2)
            )
            center_y_marker1 = (
                self.corners[self.index1][0][0][1]
                + self.corners[self.index1][0][1][1]
                + self.corners[self.index1][0][2][1]
                + self.corners[self.index1][0][3][1]
            ) / 4
            center_y_marker2 = (
                self.corners[self.index2][0][0][1]
                + self.corners[self.index2][0][1][1]
                + self.corners[self.index2][0][2][1]
                + self.corners[self.index2][0][3][1]
            ) / 4
            vangle_to_marker1 = abs(
                self.vdegrees_per_pixel * (center_y_marker1 - self.frame_height / 2)
            )
            vangle_to_marker2 = abs(
                self.vdegrees_per_pixel * (center_y_marker2 - self.frame_height / 2)
            )
            real_focal_legth1 = (
                self.focal_length
                + (hangle_to_marker1 / 30) * (self.focal_length30H - self.focal_length)
                + (vangle_to_marker1 / 30) * (self.focal_length30V - self.focal_length)
            )
            real_focal_legth2 = (
                self.focal_length
                + (hangle_to_marker2 / 30) * (self.focal_length30H - self.focal_length)
                + (vangle_to_marker2 / 30) * (self.focal_length30V - self.focal_length)
            )
            width_of_marker1 = (
                (
                    self.corners[self.index1][0][1][0]
                    - self.corners[self.index1][0][0][0]
                )
                + (
                    self.corners[self.index1][0][2][0]
                    - self.corners[self.index1][0][3][0]
                )
            ) / 2
            width_of_marker2 = (
                (
                    self.corners[self.index2][0][1][0]
                    - self.corners[self.index2][0][0][0]
                )
                + (
                    self.corners[self.index1][0][2][0]
                    - self.corners[self.index1][0][3][0]
                )
            ) / 2

            # distanceToAR = (knownWidthOfMarker(20cm) * focalLengthOfCamera) / pixelWidthOfMarker
            distance_to_marker1 = (
                self.known_marker_width * real_focal_legth1
            ) / width_of_marker1
            distance_to_marker2 = (
                self.known_marker_width * real_focal_legth2
            ) / width_of_marker2
            print(f"1: {distance_to_marker1}, 2: {distance_to_marker2}")
            self.distance_to_marker = (distance_to_marker1 + distance_to_marker2) / 2

        return True

    """
    id1 is the marker you want to look for
    specify id2 if you want to look for a gate
    cameras=number of cameras to check. -1 for all of them
    """

    # findMarker
    def find_marker(self, id1, id2=-1, cameras=-1):
        if cameras == -1:
            cameras = len(self.caps)

        for i in range(cameras):
            ret, frame = self.caps[i].read()
            if self.marker_found(id1, frame, id2=id2):
                return True

        return False

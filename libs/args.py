from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from typing import Union, List
from loguru import logger

from libs.coordinate import Coordinate


@dataclass
class Args:
    aruco_id: Union[int, None]  # the ArUco tag ID to search for, if any
    coord_file_path: str  # a file that's in the format: `lat lon`, each on a new line
    coordinate_list: List[Coordinate]
    camera_id: int  # the camera to use. defaults to 0

    def __init__(self):
        """
        Gets the command line arugments and updates internal state.
        """
        arg_parser = ArgumentParser()

        # get opencv camera id
        arg_parser.add_argument(
            "--camera_id",
            "-c",
            required=False,
            default=0,
            type=int,
            help="The OpenCV capture device (camera) ID to use. Use `tools/camera_list.py` to determine usable values.",
        )

        # get the coordinate file path
        arg_parser.add_argument(
            "--coords",
            "-f",
            required=True,
            type=str,
            help="A file path pointing to a list of coordinates. The file should have one coordinate pair per line, in this format: `lat long`",
        )

        # get the aruco ID to use
        arg_parser.add_argument(
            "--aruco_id",
            "-a",
            required=False,
            type=int,
            help="The ArUco ID number to use from the DICT_4X4_50 list. Safe testing values are 0 and 1.",
        )

        # place all data into internal state
        args: Namespace = arg_parser.parse_args()

        self.aruco_id = args.aruco_id
        if type(self.aruco_id) is not None and (
            self.aruco_id > 50 or self.aruco_id < 0
        ):
            logger.error(
                f"You must pass an ArUco ID within the range: [0, 50]. You gave: `{self.aruco_id}`."
            )
            exit(1)

        self.camera_id = args.camera_id if args.camera_id else 0

        self.coord_file_path = args.coords
        coordinate_list = []

        with open(self.coord_file_path) as file:
            for line in file:
                try:
                    (lat_str, lon_str) = line.split(" ")

                    # attempt to parse the strings into two numbers
                    (lat, lon) = (
                        float(lat_str.replace("\ufeff", "")),
                        float(lon_str.replace("\ufeff", "")),
                    )
                    
                    # create a `Coordinate` from the data
                    coordinate_list.append(Coordinate(lat, lon))
                except ValueError as e:
                    logger.error(
                        f"Failed to parse given coordinate file. Failed with error: `{e}`"
                    )
                    exit(1)
                    
            file.close()
            self.coordinate_list = coordinate_list
            logger.info(f"The coordinates file was parsed successfully! Here's the list: {self.coordinate_list}")


        pass

    pass

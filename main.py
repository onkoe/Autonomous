import argparse
from libs import udp_out
from libs.drive import Drive
import threading
from time import sleep
from typing import Tuple
from loguru import logger
from pathlib import Path
from configparser import ConfigParser


def flash(mbedIP: str, mbedPort: int) -> None:
    """
    Flash the LED colors green.

    This is used to show that the rover successfully navigated to a goal.
    """
    while True:
        udp_out.send_LED(mbedIP, mbedPort, "g")
        sleep(0.2)
        udp_out.send_LED(mbedIP, mbedPort, "o")
        sleep(0.2)


# Create Argument Parser and parse arguments
arg_parser = argparse.ArgumentParser()
arg_parser.add_argument(
    "--cameraid",
    type=int,
    help="takes an opencv number representing which camera to use",
    required=True,
)
arg_parser.add_argument(
    "--coords",
    type=str,
    help="a file that has lines of `lat long` separated by spaces",
    required=True,
)
arg_parser.add_argument(
    "--ids",
    type=int,
    help="takes two aruco ids. If you are only looking for one aruco id, the second id should be -1",
    nargs="+",
    required=True,
)
args = arg_parser.parse_args()


# TODO: dataclass this function. returning a tuple is ugly and begging for bugs
def parse_arguments() -> Tuple[list[int], list[Tuple[float, float]]]:
    """
    Parses the command line arguments.

    The returned tuple contains:
        - list[int]: the ARUCO ids we'll look for
        - list[Tuple[float, float]]: the GPS coordinates we'll drive to
    """

    # TODO: refactor `id_list` to use None/pattern matching
    # the ARUCO tag ids that we're looking for
    aruco_ids: list[int] = [-1, -1]
    # coords to drive to (tuple: lat, long)
    gps_coordinates: list[Tuple[float, float]] = []

    # make sure we have two ARUCO ids
    if len(aruco_ids) != 2:
        raise Exception(
            "Error while attempting to parse ARUCO IDs. Please enter 2 IDs to search for."
        )
    # Assign Aruco IDs
    aruco_ids = args.ids.copy()

    # handle the list of coordinates
    with open(args.coords) as file:
        for line in file:
            try:
                (lat_str, long_str) = line.split(" ")

                # attempt to parse the strings into two numbers
                coordinates: Tuple[float, float] = (
                    float(lat_str.replace("\ufeff", "")),
                    float(long_str.replace("\ufeff", "")),
                )

                # if we made it through, add them to the list
                gps_coordinates.append(coordinates)

            except ValueError as e:
                raise Exception(
                    f"Coordinate parsing failed on line: {line}. Error: {e}"
                )

        file.close()  # important: gotta close the handle

    logger.info(f"Found the following list of coordinates: {gps_coordinates}")
    return (aruco_ids, gps_coordinates)


# Gets a list of coordinates from user and drives to them and then tracks the tag
# Set id1 to -1 if not looking for a tag
# TODO: make this a part of a `Rover` class :3
def drive(
    rover: Drive, gps_coordinates: list[Tuple[float, float]], aruco_ids: list[int]
) -> bool:
    """
    Given a Drive object, navigate to goal

    return True if we make it the goal and False if we do not
    """

    # Drive along GPS coordinates
    rover.drive_along_coordinates(gps_coordinates, aruco_ids[0], aruco_ids[1])

    # TODO: Can we have this run in the rover class instead of returning from 'drive_along_coordinates'
    if aruco_ids[0] == -1:
        rover.track_AR_Marker(aruco_ids[0], aruco_ids[1])

    return True
    # TODO: Return False? If we don't make it?


if __name__ == "__main__":
    # Try to read from configuration file
    config: ConfigParser = ConfigParser(allow_no_value=True)
    if not config.read("config.ini"):
        raise Exception(
            f"Failed to open configuration file! Please ensure `config.ini` exists in this directory ({Path.cwd()})."
        )

    # Get MBED IP and MBED Port
    mbed_ip: str = str(config["CONFIG"]["MBED_IP"])
    mbed_port: int = int(config["CONFIG"]["MBED_PORT"])

    # Read command line arguments
    aruco_ids, gps_coordinates = parse_arguments()

    # Initailze REMI!!
    rover: Drive = Drive(50, args.cameraid)

    udp_out.send_LED(
        mbed_ip, mbed_port, "r"
    )  # Change the LED to red to show REMI is entering Autonomous mode

    # Drive to our goal and if we succeed, flash the LEDs green
    if drive(rover, gps_coordinates, aruco_ids):
        logger.info("Made it to the goal! Flash the LEDs green!")
        lights = threading.Thread(target=lambda: flash(mbed_ip, mbed_port))
        lights.start()
        input("Press enter to end flashing lights")
        exit()
    else:
        logger.info("!!!YOU FAILED!!!")

from dataclasses import dataclass
from socket import socket as Socket  # fixes namespace collisions

from loguru import logger


@dataclass()
class Communication:
    """
    Communicate wheel speeds and LED commands to proper micro-controllers
    """

    socket: Socket

    # constant values to define wheel speeds
    WHEEL_SUBSYSTEM_BYTE = 0x01
    WHEEL_PART_BYTE = 0x01

    # LED subsystem constants
    LED_SUBSYSTEM_BYTE = 0x01
    LED_PART_BYTE = 0x02

    def __init__(self, rover_ip: str, rover_port: int):
        self.socket = Socket(Socket.AF_INET, Socket.SOCK_DGRAM)
        self.socket.connect((rover_ip, rover_port))  # adds ip/port to socket's state

    def send_simple_wheel_speeds(self, left_speed: int, right_speed: int):
        """
        Sends the given wheel side speeds to the rover. In this case, each
        side uses the same speed for all their wheels.
        """

        (ls, rs) = (left_speed, right_speed)
        if ls < 0 or ls > 255 or rs < 0 or rs > 255:
            logger.error("HEY, speeds are wrong! `{ls}` and `{rs}` must be in [0, 255]")

        self.send_wheel_speeds(ls, ls, ls, rs, rs, rs)

    def send_wheel_speeds(
        self,
        front_left: int,
        middle_left: int,
        rear_left: int,
        front_right: int,
        middle_right: int,
        rear_right: int,
    ):
        """
        Sends the given wheel speeds to the rover. Each wheel speed goes from
        0 to 255 (u8::MAX), with 126 being neutral.
        """
        message: bytearray = bytearray(9)  # the wheels use 9 bytes

        # add subsystem and part bytes
        message.extend([self.WHEEL_SUBSYSTEM_BYTE, self.WHEEL_PART_BYTE])

        # stick in the speeds
        message.extend(
            [front_left, middle_left, rear_left, front_right, middle_right, rear_right]
        )

        # compute + add checksum
        checksum = self.__checksum(message)
        message.extend([checksum])

        # send the message over udp 🥺
        # TODO: consider using Google's QUIC instead!
        self.socket.sendall(message)
        logger.info(f"Sending wheel speeds: {self.__prettyprint_byte_array(message)}")

    def send_led_command(self, red: int, green: int, blue: int):
        """
        Sends the given LED color to the rover. All colors should be in the
        range of [0, 255].

        These are not checksummed.
        """
        message: bytearray = bytearray(5)  # LEDs use 5 bytes
        message.extend([self.LED_SUBSYSTEM_BYTE, self.LED_PART_BYTE])
        message.extend([red, green, blue])
        self.socket.sendall(message)

        pass

    def send_led_red(self):
        """Makes the LEDs red."""
        self.send_led_command(255, 0, 0)

    def send_led_green(self):
        """Makes the LEDs green."""
        self.send_led_command(0, 255, 0)

    def send_led_blue(self):
        """Makes the LEDs blue."""
        self.send_led_command(0, 0, 255)

    def __checksum(self, byte_array: bytearray) -> int:
        """
        Calculates the checksum of a byte array.
        """
        checksum: int = sum(byte_array) & 0xFF
        return checksum

    def __prettyprint_byte_array(self, byte_array: bytearray) -> str:
        """
        Prints a byte array in a human-readable format.
        """
        pretty_print: str = "["
        for index, byte in enumerate(byte_array):
            pretty_print += f"0x{byte:02X}"
            if index != len(byte_array) - 1:
                pretty_print += ", "
        pretty_print += "]"
        return pretty_print

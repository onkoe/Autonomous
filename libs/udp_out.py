import socket


def send_UDP(HOST, PORT, message):
    # sends a message over UDP to a specific host and port
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect((HOST, PORT))
        s.sendall(message)
    # sendWheelSpeeds


def send_wheel_speeds(HOST, PORT, fl, ml, rl, fr, mr, rr):
    # sends a udp message containing the six different wheel speeds.
    # arguments correspond to front left (fl), middle left (ml), etc.
    msg = bytearray(9)

    # start byte is the # character
    msg[0] = 0x01
    # byte to tell us what type of message it is.
    msg[1] = (
        0x01  # using hexadecimal since if the code changes, it will likely have to be in hex
    )

    # Add the speeds to the message, while simultaneously summing them for the verification bit
    speeds = [fl, ml, rl, fr, mr, rr]

    # Adjust speed
    speed_fix = []
    for i in speeds:
        x = (i / 90.0 + 1) * 126
        speed_fix.append(int(x))

    cs = 0
    for i in range(6):
        msg[i + 2] = speed_fix[i]
        cs += speed_fix[i]

        # add verification bit
        msg[8] = cs & 0xFF  # capped at 8 binary characters of length

    # send wheel speeds
    # sendUDP
    send_UDP(HOST, PORT, msg)
    # send_LED


def send_LED(HOST, PORT, color):
    red = 0
    green = 0
    blue = 0
    msg = bytearray(5)
    msg[0] = 0x01
    msg[1] = 0x02
    if color == "r":
        red = 255
    elif color == "g":
        green = 255
    elif color == "b":
        blue = 255
    msg[2] = red
    msg[3] = green
    msg[4] = blue
    send_UDP(HOST, PORT, msg)


if __name__ == "__main__":
    speed = -90
    send_LED(
        "192.168.1.",
        1001,
    )

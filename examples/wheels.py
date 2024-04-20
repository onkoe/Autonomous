from time import sleep
from libs import udp_out

HOST = "192.168.1.101"
# 127.0.0.1 is the 'loopback' address, or the address
# of your own computer

PORT = 1001
# this number is arbitrary as long as it is above 1024
speed = 90

udp_out.send_wheel_speeds(HOST, PORT, speed, speed, speed, speed, speed, speed)
# the six arguments represent each wheels speed (on a scale between 0 and 255, since it will be stored in a byte).
# the order of the wheels in the arguments is Front Left, Middle Left, Rear Left, Front Right, Middle Right, and Rear Right.
# sendWheelSpeeds(HOST, PORT, fl, ml, rl, rt, mr, rr)

if __name__ == "__main__":
    print("Sup")
    speed = 90
    while True:
        udp_out.send_wheel_speeds(HOST, PORT, speed, speed, speed, speed, speed, speed)
        sleep(1)

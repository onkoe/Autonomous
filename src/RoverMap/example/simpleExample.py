import os
from random import randint
import threading
import sys
from server import MapServer

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append("../")


if __name__ == "__main__":
    mapServer = MapServer()
    mapServer.register_routes()
    mapServer.start()

    def set_interval(func, sec):
        def func_wrapper():
            set_interval(func, sec)
            func()

        t = threading.Timer(sec, func_wrapper)
        t.start()
        return t

    def update():
        print("sending update...")
        mapServer.update_rover_coords([38.4375 + randint(0, 100) / 10000, -110.8125])

    print("setting interval")
    set_interval(update, 0.500)

import threading
import sys

sys.path.append("../../Mission Control/RoverMap/")
from server import MapServer
from libs import location

if __name__ == "__main__":
    loc = location.Location("10.0.0.222", "55556")
    print("Starting GPS")
    loc.start_GPS()
    loc.start_GPS_thread()

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
        # mapServer.update_rover_coords([38.4375 + randint(0, 100) / 10000 , -110.8125])
        mapServer.update_rover_coords([loc.latitude, loc.longitude])

    set_interval(update, 0.500)

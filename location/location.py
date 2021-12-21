import sys
sys.path.append('../')
from gps import gps
from math import cos, sin, atan2, pi, sqrt
from threading import Thread
from time import sleep

class Location:
    def __init__(self):
        self.swift_IP = ""
        self.swift_port = ""
        self.latitude = 0
        self.longitude = 0
        self.old_latitude = 0
        self.old_longitude = 0
        self.height = 0
        self.time = 0
        self.error = 0
        self.bearing = 0.0
        self.running = True
        self.all_zero = True
        self.wait_time = 1

    def config(self):
        # read from a file, probably configure this to work with
        # ConfigParser because that's ez
        pass

    def distance_to(self, lat:float, lon:float):
        earth_radius = 6371.301
        delta_lat = (lat - self.latitude) * (pi/180.0)
        delta_lon = (lon - self.longitude) * (pi/180.0)

        a = sin(delta_lat/2) * sin(delta_lat/2) + cos(self.latitude * (pi/180.0)) * cos(lat * (pi/180.0)) * sin(delta_lon/2) * sin(delta_lon/2)
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return earth_radius * c

    def bearing_to(self, lat:float, lon:float):
        resultbearing = self.calc_bearing(self.latitude, self.longitude, lat, lon)
        return resultbearing + 360 if resultbearing < -180 else (resultbearing - 360 if resultbearing > 180 else resultbearing)

    def start_GPS_thread(self):
        self.running = True
        t = Thread(target=self.update_fields_loop, name=(
                'update GPS fields'), args=())
        t.daemon = True
        t.start()

    def stop_GPS_thread(self):
        self.running = False

    def start_GPS(self):
        # check the config for the swift ip and port
        # connect to it w gps_init
        gps.gps_init(self.swift_IP, self.swift_port)
        print("starting data reading thread")
        self.start_GPS_thread()

    def stop_GPS(self):
        self.running = False
        gps.gps_finish()        
    
    def update_fields_loop(self):
        while(self.running):
            if gps.get_latitude() + gps.get_longitude() != 0:
                self.old_latitude = self.latitude
                self.old_longitude = self.longitude

                self.latitude = gps.get_latitude()
                self.longitude = gps.get_longitude()
                self.height = gps.get_height()
                self.time = gps.get_time()
                self.error = gps.get_error()
                self.bearing = self.calc_bearing(self.old_latitude, self.old_longitude, self.latitude, self.longitude)
                self.all_zero = False
            else:
                all_zero = True
            # maybe print info or sleep or something idk
            sleep(self.wait_time)
        return

    def calc_bearing(lat1:float, lon1:float, lat2:float, lon2:float):
        x = cos(lat2 * (pi/180.0)) * sin((lon2-lon1) * (pi/180.0))
        y = cos(lat1 * (pi/180.0)) * sin(lat2 * (pi/180.0)) - sin(lat1 * (pi/180.0)) * cos(lat2 * (pi/180.0)) * cos((lon2-lon1) * (pi/180.0))
        return (180.0/pi) * atan2(x,y)

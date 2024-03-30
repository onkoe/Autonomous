from time import sleep
from ..src.libs import Location

# os.chdir(os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    loc = Location.Location("10.0.0.222", "55556")
    print("starting gps")
    loc.start_GPS()
    loc.start_GPS_thread()
    print("reading data")
    while True:
        print(loc.latitude)
        print(loc.longitude)
        print(loc.bearing)
        print()
        sleep(1)

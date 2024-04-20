from time import sleep
from libs.location import Location

# os.chdir(os.path.dirname(os.path.abspath(__file__)))
if __name__ == "__main__":
    locator = Location("192.168.1.222", "55556")
    print("starting gps")
    locator.start_GPS()
    locator.start_GPS_thread()
    print("reading data")
    while True:
        print("latitude:", locator.latitude)
        print("longitude:", locator.longitude)
        print("bearing:", locator.bearing)
        print()
        sleep(1)

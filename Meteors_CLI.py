import ephem
from datetime import datetime
from Meteors import Meteors

class Meteors_CLI():
    """Creates a command-line interface for the meteor prediction program."""

    def __init__(self):
        self.Meteors = Meteors(self._set_observer)

    def _set_observer(self):
        """Sets the observer's time, date, latitude, longitude, and altitude."""

        # Ask for time, date, latitude, longitude, altitude
        observer = ephem.Observer()

        print("Fill out the date of observation:")
        year = int(input('Year: '))
        month = int(input('Month: '))
        day = int(input('Day: '))
        print("Fill out the time of observation (in 24-hour UTC):")
        hours = int(input('Hour: '))
        minutes = int(input('Minutes: '))

        date_and_time = datetime(year, month, day, hours, minutes)
        observer.date = ephem.Date(date_and_time)

        print("Fill out the latitude and longitude of your location, in degrees: ")
        observer.lat = str(input("Latitude: "))
        observer.lon = str(input("Longitude (negative if West): "))

        print("Fill out the altitude of your observing location, in meters: ")
        observer.elevation = int(input("Altitude: "))

        self.Meteors = Meteors(observer)

    def run(self):
        self.Meteors.run()

if __name__ == "__main__":
    CLI = Meteors_CLI()
    CLI.run()
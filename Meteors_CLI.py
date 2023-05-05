import ephem
from datetime import datetime
from Meteors import Meteors
from CustomErrors import APIError

class Meteors_CLI():
    """Creates a command-line interface for the meteor prediction program."""

    def __init__(self):
        """Initializes the Meteors object with the inputted observer information."""

        self.Meteors = Meteors(self._set_observer())

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

        return observer

    def run(self):
        try:
            num_meteors_visible = self.Meteors.run()
            print("An average of " + str(int(round(num_meteors_visible))) + " meteor(s) will be visible per hour.")
        except APIError as response_code:
            print("Oops! Our light pollution data grabber is down right now. We may have exceeded the \
                    maximum number of allowed API requests for the day, or something else might be wrong. \
                    Please try again later. Error code: " + str(response_code))

if __name__ == "__main__":
    CLI = Meteors_CLI()
    CLI.run()
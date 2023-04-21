import numpy as np
import pandas as pd
import ephem
from SkyBrightnessAndLightPollution import limiting_magnitude

class Sky():
    """Holds the ephemeral data for all meteor sources. Holds an observer object."""

    def __init__(self):
        self.observer = self._set_observer()
        self.shower_csv = pd.read_csv('ShowerData.csv')
        self.shower_csv.index = np.array(self.shower_csv["Code"], dtype=str)
        self._initialize_meteors()
        self._initialize_meteor_periods()

    def _solar_lon_to_day(self, solar_lon):
        """Converts solar longitude to the day number."""

        tropical_year = 365.2422 # days
        day_num = (solar_lon / 360) * tropical_year
        return day_num
    
    def _day_to_solar_lon(self, day_num):
        """Converts day number to solar longitude."""

        tropical_year = 365.2422 # days
        solar_lon = (day_num / tropical_year) * 360
        return solar_lon

    def _initialize_meteors(self):
        """Sets up the meteor shower radiants."""

        # accesses local variables so that I can create new ones with string names
        ephem_list = []
        for index, shower in self.shower_csv.iterrows():
            ephem_radiant = ephem.FixedBody()
            ephem_radiant._ra = ephem.hours(shower["R.A."] + ":00")
            ephem_radiant._dec = ephem.degrees(shower["Dec."][:-1])
            ephem_list.append(ephem_radiant)
        self.shower_csv["Ephem"] = ephem_list
    
    def _gaussian(self, height, mean, stddev):
        def gaussian(x):
            return height * np.exp(- ((x - mean)**2) / (2 * stddev**2))
        return gaussian
    
    def _initialize_meteor_periods(self):
        """Returns the gaussian function that represents the change in meteor number over the course of a shower.
        The sigma of each gaussian is five days, and it is centered on the day of peak solar longitude."""

        five_day_solar_lon = self._day_to_solar_lon(5)
        showers_periods = []
        for index, shower in self.shower_csv.iterrows():
            max_peak_ZHR = self.shower_csv["Max ZHR"]
            peak_solar_lon = shower["Maximum S.L."]
            gaussian = self._gaussian(max_peak_ZHR, peak_solar_lon, five_day_solar_lon)
            showers_periods.append(gaussian)
        self.shower_csv["Gaussian"] = showers_periods
    
    def _set_observer(self):
        """Sets the observer's time, date, latitude, longitude, and altitude."""

        observer = ephem.Observer()
        # these must be strings in order for ephem to use them correctly
        observer.lat = str(input("Latitude: "))
        observer.lon = str(input("Longitude: "))
        observer.elevation = input("Altitude (meters): ")
        observer.date = "DO THIS" # grab the datetime to ephem conversion
        self.observer = observer

    def change_datetime(self):
        """Changes just the date and time of the observer, without having to reset the entire observer."""
        self.observer.date = "CHANGED THING" # grab the datetime to ephem conversion

    def run(self):
        """Starts the meteor prediction program."""

        # Ask for time, date, latitude, longitude, altitude
        observer = ephem.Observer()

    def _ZHR_local(self, shower):
        """Takes an an ephem meteor shower object and calculates local ZHR."""

        limiting_mag = limiting_magnitude(self.observer)
        # the ZHR_local equation is only defined for limiting magnitudes 6.5 and brighter.
        if limiting_mag > 6.5:
            limiting_mag = 6.5
        ZHR_local = shower["ZHR"] * (np.sin(self.observer.elevation)) / (shower["r"] ** (6.5 - limiting_mag))
        return ZHR_local
    
    def _is_shower_active(self, shower):
        """Checks if the shower is active at time of observation."""

        sun = ephem.Sun()
        sun.compute(self.observer)
        solar_longitude = sun.ra

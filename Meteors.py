import numpy as np
import pandas as pd
import ephem
from datetime import datetime, timedelta
import streamlit as st
import matplotlib.pyplot as plt
from SkyBrightnessAndLightPollution import astronomical_twilight, moon_sky_brightness, light_pollution
import matplotlib.colors

class Meteors():
    """Holds the ephemeral data for all meteor sources. Holds an observer object."""

    def __init__(self, observer):
        """Initializes the observer and sets up the meteor shower data."""

        self.observer = observer
        self.shower_csv = pd.read_csv('ShowerData.csv')
        self.shower_csv.index = np.array(self.shower_csv["Code"], dtype=str)
        self._initialize_meteors()
        self._initialize_meteor_periods()
        # this value will be used for the 7-day prediction, so that the API isn't re-queried
        self._light_pollution = light_pollution(self.observer)

    # for use in future updates
    def update_observer_time(self, new_datetime):
        """Updates the observer's time of observation without having to requery the light pollution API."""

        self.observer.date = ephem.Date(new_datetime)

    def _solar_lon_to_day(self, solar_lon):
        """Converts solar longitude to the day number."""

        tropical_year = 365.2422 # days
        day_num = (solar_lon / 360) * tropical_year
        return day_num
    
    # this is a simplified version of solar longitude that ignores the ellipticity of Earth's orbit
    def _day_to_solar_lon(self, day_num):
        """Converts day number to solar longitude."""

        tropical_year = 365.2422 # days
        solar_lon = (day_num / tropical_year) * 360
        return solar_lon

    def _initialize_meteors(self):
        """Sets up the meteor shower radiants with ephem."""

        ephem_list = []
        for index, shower in self.shower_csv.iterrows():
            ephem_radiant = ephem.FixedBody()
            ephem_radiant._ra = ephem.hours(shower["R.A."] + ":00")
            ephem_radiant._dec = ephem.degrees(shower["Dec."][:-1])
            ephem_list.append(ephem_radiant)
        self.shower_csv["Ephem"] = ephem_list
    
    def _gaussian(self, height, mean, stddev):
        """Returns a callable gaussian function with the specified height, mean, and standard deviation."""

        def gaussian(x):
            return height * np.exp(-1 * ((x - mean)**2) / (2 * stddev**2))
        return gaussian
    
    def _initialize_meteor_periods(self):
        """Returns the gaussian function that represents the change in meteor number over the course of a shower.
        The sigma of each gaussian is five days, and it is centered on the day of peak solar longitude."""

        five_day_solar_lon = self._day_to_solar_lon(5)
        showers_periods = []
        for index, shower in self.shower_csv.iterrows():
            max_peak_ZHR = shower["Max ZHR"]
            peak_solar_lon = shower["Maximum S .L."]
            gaussian = self._gaussian(max_peak_ZHR, peak_solar_lon, five_day_solar_lon)
            showers_periods.append(gaussian)
        self.shower_csv["Gaussian"] = showers_periods

    def _meteor_number_info(self, limiting_mag, active_shower_codes):
        """Provides info to an observer on light pollution, moon phase, and active meteor showers."""

        # bortle class
        if limiting_mag >= 7.6:
            bortle_class = 1
        elif limiting_mag >= 7.1:
            bortle_class = 2
        elif limiting_mag >= 6.6:
            bortle_class = 3
        elif limiting_mag >= 6.3:
            bortle_class = 4
        elif limiting_mag >= 5.6:
            bortle_class = 5
        elif limiting_mag >= 5.1:
            bortle_class = 6
        elif limiting_mag >= 4.6:
            bortle_class = 7
        elif limiting_mag <= 4:
            bortle_class = "8 or 9"

        # active showers
        if len(active_shower_codes) == 0:
            active_showers = "There are no active meteor showers on your selected date."
        else:
            active_showers = "The active meteor showers on your selected date are: "
            for index, shower_code in enumerate(active_shower_codes):
                if index+1 != len(active_shower_codes):
                    active_showers += str(self.shower_csv.at[shower_code, "Shower"])
                    active_showers += ", "
                else:
                    if index != 0:
                        active_showers += " and "
                    active_showers += str(self.shower_csv.at[shower_code, "Shower"])
                    active_showers += "."

        # Percent illumination of the moon
        ___, moon_illumination, moon_alt = moon_sky_brightness(self.observer)

        moon_message = "The moon's brightness can greatly decrease the number of meteors visible, and this \
            has been factored into your prediction. "
        if moon_alt > 0:
            moon_message += "The Moon will be up at your selected time, and it will be " + str(round(moon_illumination, 1)) + \
                " percent illuminated."
        else:
            moon_message += "The Moon will be " + str(round(moon_illumination, 1)) + " percent illuminated, \
                but it won't be up at your selected time."

        return active_showers, bortle_class, moon_message
    
    def _sqm_to_bortle_to_limiting_mag(self, sqm):
        """Converts mags per square arcsecond into Bortle class, and returns the corresponding limiting magnitude."""

        if sqm >= 21.75:
            return 7.6
        elif sqm >= 21.6:
            return 7.1
        elif sqm >= 21.3:
            return 6.6
        elif sqm >= 20.8:
            return 6.3
        elif sqm >= 20.3:
            return 6.1
        elif sqm >= 19.25:
            return 5.6
        elif sqm >= 18.5:
            return 5.1
        elif sqm >= 18.00:
            return 4.6
        else: # this is both classes 8 and 9
            return 4
    
    def _limiting_magnitude(self, use_moon=True):
        """Returns limiting magnitude by calculating the sky brightness in mags per square arcsecond, and then
        converting to the Bortle scale, and then to limiting magnitude. Takes into account both light pollution
        and the Moon phase brightness."""

        if use_moon:
            moon_mag, __, moon_alt = moon_sky_brightness(self.observer)
            if moon_mag < self._light_pollution and moon_alt > 0: # smaller magnitudes are brighter
                sky_mag = moon_mag
            else:
                sky_mag = self._light_pollution
        else:
            sky_mag = self._light_pollution

        limiting_mag = self._sqm_to_bortle_to_limiting_mag(sky_mag)
        return limiting_mag

    def _ZHR_local(self, return_meteor_info=False):
        """Calculates local visible rates for all meteor sources combined."""

        limiting_mag = self._limiting_magnitude()
        # the ZHR_local equation is only defined for limiting magnitudes 6.5 and brighter.
        if limiting_mag > 6.5:
            limiting_mag = 6.5
        # if not astronomical twilight, the limiting mag should be ignored
        if not astronomical_twilight(self.observer):
            limiting_mag = 0 

        sun = ephem.Sun()
        sun.compute(self.observer)
        solar_longitude = np.degrees(sun.ra)
        total_visible_meteors = 0
        active_shower_codes = []
        for index, shower in self.shower_csv.iterrows():
            meteor_function = shower["Gaussian"]
            num_meteors = meteor_function(solar_longitude)
            if round(num_meteors, 0) > 0:
                active_shower_codes.append(shower["Code"])
            shower["Ephem"].compute(self.observer)
            shower_alt = shower["Ephem"].alt  # this is in radians
            if shower_alt > 0:
                ZHR_local = num_meteors * (np.sin(shower_alt)) / (shower["r"] ** (6.5 - limiting_mag))
            else:
                ZHR_local = 0
            total_visible_meteors += ZHR_local
        sporadics = self._max_sporadic_meteors()
        # r = 3 for anthelion meteors, and we assume the radiant is the zenith (since sporadics have no true radiant)
        visible_sporadics = sporadics * (np.sin(90)) / (3 ** (6.5 - limiting_mag))
        total_visible_meteors += visible_sporadics

        if return_meteor_info == True:
            active_showers, bortle_class, moon_illumination = self._meteor_number_info(self._limiting_magnitude(use_moon=False), active_shower_codes)
            return total_visible_meteors, active_showers, bortle_class, moon_illumination
        else:
            return total_visible_meteors
    
    def seven_day_prediction(self):
        """Returns a graph of the 7-day local visible meteor numbers."""

        current_datetime = self.observer.date.datetime()
        num_meteors_visible = []
        solar_altitude = []
        lunar_phase = []
        lunar_altitude = []
        # three days worth of hours, evaluated every fifteen minutes
        hours = np.arange(0, 3*24, 0.25)
        times = []
        for hour_number in hours:
            test_observer = self.observer
            new_date = current_datetime + timedelta(hours=hour_number)
            times.append(new_date)
            test_observer.date = new_date
            
            sun = ephem.Sun()
            sun.compute(test_observer)
            solar_altitude.append(np.degrees(sun.alt))

            ____, moon_phase, moon_alt = moon_sky_brightness(self.observer)
            lunar_phase.append(moon_phase)
            lunar_altitude.append(np.degrees(moon_alt))

            # if sun is at the wrong altitude, then no meteors are visible
            if not astronomical_twilight(test_observer):
                num_meteors_visible.append(0)
            else:
                solar_longitude = np.degrees(sun.ra)
                total_visible_meteors = 0
                limiting_mag = self._limiting_magnitude()
                # the ZHR equation is not defined for limiting mags > 6.5
                if limiting_mag > 6.5:
                    limiting_mag = 6.5
                for index, shower in self.shower_csv.iterrows():
                    meteor_function = shower["Gaussian"]
                    num_meteors = meteor_function(solar_longitude)
                    shower["Ephem"].compute(test_observer)
                    shower_alt = shower["Ephem"].alt  # this is in radians
                    if shower_alt > 0:
                        ZHR_local = num_meteors * (np.sin(shower_alt)) / (shower["r"] ** (6.5 - limiting_mag))
                    else:
                        ZHR_local = 0
                    total_visible_meteors += ZHR_local
                sporadics = self._max_sporadic_meteors()
                # r = 3 for anthelion (sporadic) meteors, and we assume the radiant is the zenith (since sporadics have no true radiant)
                visible_sporadics = sporadics * (np.sin(90)) / (3 ** (6.5 - limiting_mag))
                total_visible_meteors += visible_sporadics
                num_meteors_visible.append(total_visible_meteors)

        # plotting
        fig, (ax1, ax2) = plt.subplots(2, figsize=(10,6), gridspec_kw={'height_ratios': [2, 3]})
        ax1.plot(times, num_meteors_visible, color="#ff4b4b", label="Meteors visible per hour")
        ax1.set_ylabel("Meteors per hour")
        ax2.set_xlabel("Month, day, and hour (in 24hr UTC)")
        ax2.plot(times, solar_altitude, label="Sun", color="orchid")
        normalize = matplotlib.colors.Normalize(vmin=0, vmax=100)
        moon_scatter = ax2.scatter(times, lunar_altitude, label="Moon", c=np.array(lunar_phase), cmap="copper", norm=normalize, s=5)
        ax2.set_ylabel("Altitude (deg)")
        plt.legend(loc='upper right')
        plt.colorbar(moon_scatter, orientation='horizontal', aspect=60, pad=0.35, label="Moon phase (0=new, 100=full)")
        return fig

    def _max_sporadic_meteors(self):
        """Returns the number of sporadic meteors per hour. This is currently a very simplified model which uses 
        the same two functions for all of the southern hemisphere and for all of the northern hemisphere. If the 
        observer is on the equator, the two models are averaged. This function will be improved in future versions."""

        # these are observed values from 45 deg north and 45 deg south
        northern_hemisphere = {1: 13, 2: 10, 3: 8, 4: 7, 5: 6, 6: 6, 7: 9, 8: 12, 9: 14, 10: 15, 11: 16, 12: 15}
        southern_hemisphere = {1: 14, 2: 13, 3: 11, 4: 13, 5: 14, 6: 16, 7: 15, 8: 9, 9: 5, 10: 5, 11: 6, 12: 11}

        month = self.observer.date.tuple()[1]
        latitude = self.observer.lat

        if latitude > 0:
            return northern_hemisphere[month]
        if latitude < 0:
            return southern_hemisphere[month]
        else:
            return (northern_hemisphere[month] + southern_hemisphere[month]) / 2
        
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

    def run(self, return_meteor_info=False):
        """Starts the meteor prediction program."""

        num_meteors_visible = self._ZHR_local(return_meteor_info)
        return num_meteors_visible

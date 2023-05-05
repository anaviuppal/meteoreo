import numpy as np
import ephem
import requests
from datetime import datetime
from CustomErrors import APIError

def mcd_to_SQM(mcd):
    """Converts brightness from mcd/m2 into mag/arcsec2."""

    return np.log10(mcd / 108000000) / (-0.4)

def light_pollution(observer):
    """Returns light pollution data from lightpollutionmap.info."""

    longitude = np.degrees(observer.lon)
    latitude = np.degrees(observer.lat)
    # the light pollution map doesn't have dadta outside of these latitudes, so I am returning the darkest sky value
    if latitude <= -60 or latitude >= 75:
        return 22.0

    KEY = "fO7PlrdDnJuE7vTN" 
    url = "https://www.lightpollutionmap.info/QueryRaster/?ql=wa_2015&qt=point&qd=" + str(longitude) + "," + str(latitude) + "&key=" + KEY
    response = requests.get(url)

    # Check if the response was successful
    if response.status_code == 200:
        artificial_brightness = response.json()
        base_brightness = 0.171168465 # mcd/m2
        total_brightness = base_brightness + artificial_brightness # in mcd/m2
        return mcd_to_SQM(total_brightness) # in mags per square arcsec
    else:
        raise APIError(response.status_code)

def astronomical_twilight(observer):
    """Checks if the observer has selected a time that is after astronomical twilight."""

    sun = ephem.Sun(observer)
    if np.degrees(sun.alt) <= -18:
        return True
    else:
        return False

#  Function for use in future code updates
def _moon_sky_brightness(observer):
    """Calculates the additional sky brightness from the moon phase."""

    # Getting moon to sky brightnesses, and subtracting the base sky brightness of 22 mags/sq arcsec

    # Checking the brightness at the observer's location

#  Function for use in future code updates
def _object_extinction(observer, object):
    """Calculates the extinction of an object's light due to the thickness of the atmosphere."""

    object_is_up = object.alt > 0
    if object_is_up:
        airmass = 1 / (np.cos(object.alt) + 0.025 * np.exp(-11 * np.cos(object.alt)))

        # total extinction = Rayleigh extinction + aerosol extinction + ozone extinction
        # apparent mag = actual visual magnitude + (total extinction * airmass)
        # Rayleigh extinction
        A_ray = 0.1451 * np.exp((-1 * observer.alt) / 7.996)
        # Aerosol extinction
        A_aer = 0.120 * np.exp((-1 * observer.alt) / 1.5)
        # Ozone extinction
        A_oz = 0.016

        A_prime = A_ray + A_aer + A_oz
        extinction = airmass * A_prime
        return extinction
    else:
        return 0
    
def sqm_to_bortle_to_limiting_mag(sqm):
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
    
def limiting_magnitude(observer):
    """Returns limiting magnitude by calculating the sky brightness in mags per square arcsecond, and then
    converting to the Bortle scale, and then to limiting magnitude."""

    light_pollution_mag = light_pollution(observer)
    limiting_mag = sqm_to_bortle_to_limiting_mag(light_pollution_mag)
    return limiting_mag
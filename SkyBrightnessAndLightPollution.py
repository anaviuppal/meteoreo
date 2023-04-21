import numpy as np
import ephem
import requests
from datetime import datetime
from CustomErrors import APIError

def mcd_to_SQM(mcd):
    """Converts brightness from mcd/m2 into mag/arcsec2."""

    return np.log10(mcd / 108000000) / (-0.4)

def _light_pollution(observer):
    """Returns light pollution data from lightpollutionmap.info."""

    longitude = observer.lon
    latitude = observer.lat
    key = "fO7PlrdDnJuE7vTN" # if I put this on github, is there still a way to keep this key private?
    url = "https://www.lightpollutionmap.info/QueryRaster/?ql=wa_2015&qt=point&qd=" + str(longitude) + "," + str(latitude) + "&key=" + key
    response = requests.get(url)

    # Check if the response was successful
    if response.status_code == 200:
        # Print the response content
        artificial_brightness = response.json()
        base_brightness = 0.171168465 # mcd/m2
        total_brightness = base_brightness + artificial_brightness # in mcd/m2
        return mcd_to_SQM(total_brightness) # in mags per square arcsec
    else:
        raise APIError(response.status_code)
    
def _sky_brightness(observer):
    """Calculates the sky brightness based on light pollution and sunlight and moonlight."""

    moon = ephem.Moon(observer.date)
    sun = ephem.Sun(observer.date)
    base_sky_brightness_mag = _light_pollution(observer)
    moon_phase = moon.phase

    # Calculate the moon's contribution to the sky brightness

    # Subtract the moon's contribution to the sky brightness

    # Calculate the sun's contribution to the sky brightness

    # Subtract the sun's contribution to the sky brightness

    # Return the sky brightness magnitude
    return sky_brightness_mag

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
    
def limiting_magnitude(observer):
    """Returns limiting magnitude by calculating the sky brightness in mags per square arcsecond and then
    converting to the Bortle scale."""

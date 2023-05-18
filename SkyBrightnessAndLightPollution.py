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

def moon_sky_brightness(observer):
    """Calculates the additional sky brightness from the moon phase."""

    # X-values must be in increasing order, otherwise np.interp returns meaningless values
    # This is [[illumination percentage], [apparent magnitude]]
    # Data is from Table 1 of M. Minnaert (1961), as shown in:
    # https://github.com/pchev/skychart/blob/98b7ac40b660beb6acd33d3d183e401e9fe76388/skychart/cu_planet.pas#L1315
    moon_illumination_mags = np.array([[0.03, 0.07, 0.12, 0.18, 0.25, 0.33, 0.41, 0.5, 0.59, 0.67, 0.75, 0.82, 
                                        0.88, 0.93, 0.97, 0.99, 1.0],
                                        [-3.4, -6.7, -7.6, -8.2, -8.7, -9.2, -9.6, -10.0, -10.4, -10.8, -11.0, 
                                        -11.2, -11.5, -11.8, -12.1, -12.4, -12.7]])
    
    moon = ephem.Moon(observer)
    # ephem returns this as a 0-100 number, so I am converting this to a percentage
    moon_illumination = moon.phase * 0.01
    moon_apparent_mag = np.interp(moon_illumination, moon_illumination_mags[0], moon_illumination_mags[1])

    # Calculating its contribution to skyglow, as specified at:
    # https://www.cloudynights.com/topic/623469-sqm-readings-during-full-moon/
    sky_brightness = moon_apparent_mag + 30.2
    return sky_brightness, moon.phase, moon.alt

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
    
"""def sqm_to_bortle_to_limiting_mag(sqm):
    Converts mags per square arcsecond into Bortle class, and returns the corresponding limiting magnitude.

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
    Returns limiting magnitude by calculating the sky brightness in mags per square arcsecond, and then
    converting to the Bortle scale, and then to limiting magnitude.

    light_pollution_mag = light_pollution(observer)
    limiting_mag = sqm_to_bortle_to_limiting_mag(light_pollution_mag)
    return limiting_mag"""
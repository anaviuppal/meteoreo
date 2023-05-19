import ephem
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium
import folium
from datetime import datetime, timezone
from Meteors import Meteors
from CustomErrors import APIError
import timezonefinder

def bortle_class_info(bortle_class):
    """Returns info about an observer's light pollution."""

    if bortle_class == 1:
        return "Your Bortle scale rating is 1, which means that your observing location is an \
                excellent dark-sky site. You can't get any better than that!"
    elif bortle_class == 2:
        return "Your Bortle scale rating is 2, which means that your observing location is a \
                typical truly dark site. That's pretty great!"
    elif bortle_class == 3:
        return "Your Bortle scale rating is 3, which means that your observing location is a \
                rural sky site. You might see some light pollution near the horizon, but otherwise, you \
                have a pretty dark sky."
    elif bortle_class == 4:
        return "Your Bortle scale rating is 4, which means that your observing location is a \
                brighter rural sky site. You can probably see light pollution from cities in the distance, but \
                your sky is still fairly dark."
    elif bortle_class == 5:
        return "Your Bortle scale rating is 5, which means that your observing location is a \
                suburban sky site. This means that you can see light pollution in most directions, and any clouds \
                are noticeably brighter than the sky."
    elif bortle_class == 6:
        return "Your Bortle scale rating is 6, which means that your observing location is a \
                bright suburban sky site. This means light pollution makes the lower sky glow \
                grayish-white, and your surroundings are easily visible."
    elif bortle_class == 7:
        return "Your Bortle scale rating is a 7, which means that your observing location is a \
                suburban/urban transition site. This means that light pollution makes the entire sky a light gray."
    elif bortle_class == "8 or 9":
        return "Your Bortle scale rating is 8 or 9, which means that your observing location is a \
            city sky site. This means that the sky is brightly lit and many constellations are weak or \
                invisible."

st.set_page_config(layout="wide")
# title and logo, with spacing to the right
col1, col2, extra = st.columns([2,2,9])
meteoreo_icon = Image.open('meteoreo_icon.png')
with col1:
    st.title('meteoreo')
with col2:
    st.image(meteoreo_icon, width=80, output_format='png')

st.markdown("How many meteors can you see per hour? Put in your observation time and location, and we'll predict \
           it for you based on random meteors, meteor showers, the altitude of the Sun, the phase of the Moon, and your local light \
           pollution.")

# the entry boxes for date and time are set to the current UTC date and time, by default
# if this isn't a session state, it causes errors where it overwrites a user's inputted time sometimes
if 'current_datetime' not in st.session_state:
    st.session_state.current_datetime = datetime.now(timezone.utc)
date_col1, date_col2, date_col3 = st.columns([2,1,1])
with date_col1:
    st.session_state.date = st.date_input("Date of observation (:red[UTC]): ", value=st.session_state.current_datetime)
with date_col2:
    st.session_state.hour = st.number_input("Hour (:red[UTC], 24-hour format): ", value=st.session_state.current_datetime.hour, min_value=0, max_value=23)
with date_col3:
    st.session_state.minute = st.number_input("Minute: ", value=st.session_state.current_datetime.minute, min_value=0, max_value=59)

map_col1, map_col2 = st.columns([1,1])
# the default location is New Haven, CT, USA
DEFAULT_LATITUDE = 41.3083
DEFAULT_LONGITUDE = -72.9279
DEFAULT_ALTITUDE = 18.0
with map_col2:
    st.session_state.latitude = DEFAULT_LATITUDE
    st.session_state.longitude = DEFAULT_LONGITUDE
    m = folium.Map(location=[st.session_state.latitude, st.session_state.longitude], zoom_start=10, max_bounds=True, min_zoom=2)

    # displays a popup with the latitude and longitude shown
    m.add_child(folium.LatLngPopup())

    f_map = st_folium(m, height=255, width=550)

    # allows the user to click the map to set the observing location
    if f_map.get("last_clicked"):
        st.session_state.latitude = f_map["last_clicked"]["lat"]
        st.session_state.longitude = f_map["last_clicked"]["lng"]

with map_col1:
    st.markdown("Click on the map to select a location or type in your latitude and longitude. Need to look up \
                your coordinates? Search for your observing location \
                at https://www.distancesto.com/coordinates.php.")
    st.session_state.latitude = st.number_input("Latitude: ", value=st.session_state.latitude, min_value=-90.0, max_value=90.0, step=0.00001, format="%f")
    st.session_state.longitude = st.number_input("Longitude (negative for West): ", value=st.session_state.longitude, min_value=-180.0, max_value=180.0, step=0.00001, format="%f")
    #st.session_state.altitude = st.number_input("Altitude (in meters): ", value=DEFAULT_ALTITUDE, min_value=0.0, max_value=8850.0, step=0.00001, format="%f")
    st.session_state.altitude = 0

# sets up the observer with the specified date, time, location
st.session_state.observer = ephem.Observer()
date_and_time = datetime(st.session_state.date.year, st.session_state.date.month, st.session_state.date.day,
                         st.session_state.hour, st.session_state.minute)
st.session_state.observer.date = ephem.Date(date_and_time)
# ephem requires latitude and longitude to be inputted as strings
st.session_state.observer.lat = str(st.session_state.latitude)
st.session_state.observer.lon = str(st.session_state.longitude)
st.session_state.observer.elevation = st.session_state.altitude

# press the submit button
if st.button('Calculate number of visible meteors'):
    meteor_object = Meteors(st.session_state.observer)
    try:
        num_meteors_visible, active_showers, bortle_class, moon_illumination = meteor_object.run(return_meteor_info=True)
    except APIError as response_code:
        st.markdown("Oops! Our light pollution data grabber is down right now. We may have exceeded the \
                    maximum number of allowed API requests for the day, or something else might be wrong. \
                    Error code: " + str(response_code))
    else:
        num_meteors_visible = int(round(num_meteors_visible, 0))
        st.subheader("You will see an average of " + str(num_meteors_visible) + " meteor(s) per hour.")
        st.markdown("If the Sun is above an altitude of -18 degrees, the sky is too bright to see most meteors, \
                    so the predictor will return 0 meteors per hour.")
        st.subheader("Here's your prediction for the next three days:")
        st.markdown("The top plot predicts how many meteors you will be able to see per hour. The bottom plot \
                    shows the altitude of the Sun and Moon. The color of the Moon circles also tell you the Moon \
                    phase: lighter colors indicate a fuller Moon. When the Moon is brighter, you can see fewer meteors.")

        fig = meteor_object.seven_day_prediction()
        st.pyplot(fig)

        st.subheader("More info about your meteor prediction: ")
        # tells which showers are currently active
        st.markdown(active_showers)
        # specifies the location's Bortle class, with additional viewing info
        st.markdown(bortle_class_info(bortle_class))
        st.markdown(moon_illumination)
        st.markdown("Want to see the most meteors possible? Make sure to be at a location where the entire \
                    sky is visible, and avoid nights when the Moon is bright. And don't forget to check the weather! \
                    These predictions are only accurate for a clear sky.")

st.caption("")
st.caption("Created by Anavi Uppal (2023). Contact anavi.uppal@yale.edu to report bugs.")
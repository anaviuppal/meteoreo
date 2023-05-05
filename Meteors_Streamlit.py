import ephem
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium
import folium
from datetime import datetime, timezone
from Meteors import Meteors

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
                brighter rural sky site. You can probably see light pollution from nearby cities, but \
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
col1, col2, extra = st.columns([2,2,9])
meteoreo_icon = Image.open('meteoreo_icon.png')
with col1:
    st.title('meteoreo')
with col2:
    st.image(meteoreo_icon, width=80, output_format='png')

st.markdown("How many meteors you can see per hour? Put in your observation time and location, and we'll calculate \
           it for you based on sporadic meteors, meteor showers, the altitude of the Sun, and your local light \
           pollution. Don't know your latitude, longitude, or altitude? Search for your observing location \
           at https://www.distancesto.com/coordinates.php.")

# the entry boxes for date and time are set to the current UTC date and time, by default
current_datetime = datetime.now(timezone.utc)
date_col1, date_col2, date_col3 = st.columns([2,1,1])
with date_col1:
    st.session_state.date = st.date_input("Date of observation (UTC): ", value=current_datetime)
with date_col2:
    st.session_state.hour = st.number_input("Hour (UTC, 24-hour format): ", value=current_datetime.hour)
with date_col3:
    st.session_state.minute = st.number_input("Minute: ", value=current_datetime.minute)

map_col1, map_col2 = st.columns([1,1])
# the default location is New Haven, CT, USA
DEFAULT_LATITUDE = 41.3083
DEFAULT_LONGITUDE = -72.9279
DEFAULT_ALTITUDE = 18.0
with map_col1:
    st.session_state.latitude = st.number_input("Latitude: ", value=DEFAULT_LATITUDE, min_value=-90.0, max_value=90.0, step=0.00001, format="%f")
    st.session_state.longitude = st.number_input("Longitude (negative for West): ", value=DEFAULT_LONGITUDE, min_value=-180.0, max_value=180.0, step=0.00001, format="%f")
    st.session_state.altitude = st.number_input("Altitude (in meters): ", value=DEFAULT_ALTITUDE, min_value=0.0, max_value=8850.0, step=0.00001, format="%f")
with map_col2:
    m = folium.Map(location=[st.session_state.latitude, st.session_state.longitude], zoom_start=10)
    marker = folium.Marker(location=[st.session_state.latitude, st.session_state.longitude], icon=folium.Icon(color='red', icon='pushpin')).add_to(m)

    # The code below will be responsible for displaying 
    # the popup with the latitude and longitude shown
    m.add_child(folium.LatLngPopup())

    f_map = st_folium(m, height=250, width=550)

    selected_latitude = DEFAULT_LATITUDE
    selected_longitude = DEFAULT_LONGITUDE

    if f_map.get("last_clicked"):
        selected_latitude = f_map["last_clicked"]["lat"]
        selected_longitude = f_map["last_clicked"]["lng"]

st.session_state.observer = ephem.Observer()
date_and_time = datetime(st.session_state.date.year, st.session_state.date.month, st.session_state.date.day,
                         st.session_state.hour, st.session_state.minute)
st.session_state.observer.date = ephem.Date(date_and_time)
# ephem requires latitude and longitude to be inputted as strings
st.session_state.observer.lat = str(st.session_state.latitude)
st.session_state.observer.lon = str(st.session_state.longitude)
st.session_state.observer.elevation = st.session_state.altitude

if st.button('Calculate number of visible meteors'):
    meteor_object = Meteors(st.session_state.observer)
    num_meteors_visible, active_showers, bortle_class = meteor_object.run(return_meteor_info=True)
    num_meteors_visible = int(round(num_meteors_visible, 0))
    st.subheader("You will see an average of " + str(num_meteors_visible) + " meteor(s) per hour.")
    st.markdown("If the Sun is above an altitude of -18 degrees, the sky will be too bright to see most meteors, \
                so the predictor will return 0 meteors per hour.")
    st.subheader("Here's your prediction for the next three days:")

    fig = meteor_object.seven_day_prediction()
    st.pyplot(fig)

    st.subheader("More info about your meteor prediction: ")
    st.markdown(active_showers)
    st.markdown(bortle_class_info(bortle_class))
    st.markdown("Want to see the most meteors possible? Make sure to be at a location where the entire \
                sky is visible, and avoid nights when the Moon is up. And don't forget to check the weather! \
                These predictions are only accurate for a clear sky.")
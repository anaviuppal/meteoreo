import ephem
from datetime import datetime, timezone
from Meteors import Meteors
import streamlit as st

st.title('meteoreo')
st.caption("Welcome to meteoreo! Want to know how many meteors you can see per hour? Put in your observation time and location, and we'll make the magic happen.")

current_datetime = datetime.now(timezone.utc)
st.session_state.date = st.date_input("Date of observation (UTC): ", value=current_datetime)
st.session_state.hour = st.number_input("Hour (UTC, 24-hour format): ", value=current_datetime.hour)
st.session_state.minute = st.number_input("Minute: ", value=current_datetime.minute)
# current problem is that the number input is snapping these values to an integer
st.session_state.latitude = st.number_input("Latitude: ", min_value=-90.0, max_value=90.0, step=0.00001, format="%f")
st.session_state.longitude = st.number_input("Longitude (negative for West): ", min_value=-180.0, max_value=180.0, step=0.00001, format="%f")
st.session_state.altitude = st.number_input("Altitude (in meters): ", value=0, min_value=0, max_value=8850)

observer = ephem.Observer()
date_and_time = datetime(st.session_state.date.year, st.session_state.date.month, st.session_state.date.day,
                         st.session_state.hour, st.session_state.minute)
observer.date = ephem.Date(date_and_time)
observer.lat = str(st.session_state.latitude)
observer.lon = str(st.session_state.longitude)
observer.elevation = st.session_state.altitude

if st.button('Calculate number of visible meteors'):
    st.session_state.num_meteors_visible = int(round(Meteors(observer).run(), 0))
    st.subheader("There will be an average of " + str(st.session_state.num_meteors_visible) + " meteor(s) visible per hour.")
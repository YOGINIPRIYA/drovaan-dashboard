import streamlit as st
import pandas as pd
import numpy as np
import requests
import datetime
import pytz

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="🌍Drovaan Dashboard", layout="wide")
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] {
    max-width: 1000px;
    margin: auto;
}
</style>
""", unsafe_allow_html=True)

# ------------------ CSS ------------------
page_bg = """
<style>
[data-testid="stAppViewContainer"] {
  background-image: url("nebula.jpg");
  background-size: cover;
  background-attachment: fixed;
  background-repeat: no-repeat;
  background-position: center center;
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg,
    #18284a 0%,
    #0a1c3f 25%,
    #2a4d9f 50%,
    #4a75d1 75%,
    #cce7ff 100%);
  color: white;
}
h2, span, div[data-testid="stSidebar"] > div {
  color: #ffffff !important;
  font-weight: bold;
}
.stButton > button {
  background: linear-gradient(180deg, #18284a, #0a1c3f, #2a4d9f, #4a75d1, #cce7ff);
  border-radius: 12px;
  border: none;
  padding: 8px 16px;
  font-weight: bold;
}
.stButton > button:hover {
  background: linear-gradient(180deg, #4a75d1, #2a4d9f, #0a1c3f);
  color: white !important;
  box-shadow: 0px 0px 12px #00eaff;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# ------------------ SIDEBAR ------------------
st.sidebar.title("🌍 Explore")

view_option = st.sidebar.selectbox(
    "Select View",
    ["Navigator", "Atmospheric view", "About"],
    key="view_option"
)
city_input = st.sidebar.text_input("Enter City Name:", value="Chennai", key="city_input")
prediction_date = st.sidebar.date_input(
    "Select Prediction Date", value=(datetime.datetime.utcnow() + datetime.timedelta(days=1)).date(),
    min_value=datetime.date.today(), key="prediction_date"
)
prediction_time = st.sidebar.time_input(
    "Select Prediction Time (UTC)", value=datetime.time(hour=12, minute=0), key="prediction_time"
)

drone_enabled = st.sidebar.checkbox("Enable Drone Data", value=False, key="drone_enabled")
if drone_enabled:
    drone_data_option = st.sidebar.selectbox("Drone Data", ["Conditions", "Data History"], index=0, key="drone_data_option")
else:
    drone_data_option = "No Drone Data"

zoom_level = None
if view_option == "Atmospheric view":
    zoom_level = st.sidebar.slider("Zoom Level", 0, 6, 2, key="zoom_level")

# ------------------ FUNCTIONS ------------------
def format_iso_datetime_to_ist(iso_str):
    if iso_str is None or iso_str == "N/A":
        return "N/A"
    try:
        dt = datetime.datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        dt = dt.replace(tzinfo=pytz.utc)
        ist = pytz.timezone("Asia/Kolkata")
        dt_ist = dt.astimezone(ist)
        return dt_ist.strftime("%I:%M %p %Y-%m-%d IST")
    except Exception:
        return iso_str

def get_coordinates(city_name):
    try:
        headers = {"User-Agent": "streamlit-weather-app"}
        response = requests.get("https://nominatim.openstreetmap.org/search",
                                params={"q": city_name, "format": "json"}, headers=headers, timeout=10)
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        st.error("Failed to get coordinates for the city.")
    return None, None

def get_weather(lat, lon, target_datetime):
    USERNAME = "annauniversity_vijayakumar_yoginipriya"
    PASSWORD = "ivUm5Q5HU1UY6Z3zCg3p"
    parameters = "t_2m:C,precip_24h:mm,wind_speed_10m:ms,uv:idx,sunrise:sql,sunset:sql"
    time_str = target_datetime.replace(microsecond=0).isoformat() + "Z"
    url = f"https://api.meteomatics.com/{time_str}/{parameters}/{lat},{lon}/json"
    response = requests.get(url, auth=(USERNAME, PASSWORD))
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Weather API error ({response.status_code}): {response.text}")
        return None

def get_nasa_gibs_image_url(lat, lon, zoom, layer_name):
    bbox_sizes = {0: 2.0, 1: 1.0, 2: 0.5, 3: 0.25, 4: 0.1, 5: 0.05, 6: 0.025}
    img_sizes = {0: 300, 1: 400, 2: 500, 3: 600, 4: 800, 5: 900, 6: 1000}
    delta = bbox_sizes.get(zoom, 0.1)
    height = img_sizes.get(zoom, 600)
    width = height
    min_lat, max_lat = lat - delta, lat + delta
    min_lon, max_lon = lon - delta, lon + delta
    date_str = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    base_url = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?"
    params = (
        f"SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS={layer_name}&"
        f"STYLES=&FORMAT=image/png&TRANSPARENT=TRUE&HEIGHT={height}&WIDTH={width}&"
        f"CRS=EPSG:4326&BBOX={min_lat},{min_lon},{max_lat},{max_lon}&TIME={date_str}"
    )
    return base_url + params

def generate_sample_drone_data(num_samples=50):
    timestamps = pd.date_range(end=pd.Timestamp.now(), periods=num_samples, freq='T')
    temperature = np.random.normal(loc=25, scale=2, size=num_samples)
    humidity = np.random.uniform(low=40, high=60, size=num_samples)
    return pd.DataFrame({"Timestamp": timestamps, "Temperature (°C)": temperature, "Humidity (%)": humidity})

# ------------------ MAIN ------------------
city = city_input.strip()
lat, lon = get_coordinates(city)

# ------------------ ABOUT ------------------
if view_option == "About":
    st.title("About Drovaan Dashboard")

    st.write("""
    The Drovaan Dashboard is an advanced hyperlocal weather prediction and atmospheric monitoring platform.
    It integrates real-time data from drone-based environmental sensors and high-resolution NASA datasets
    to provide accurate and localized weather insights.

    This system combines hyperlocal sensor readings with large-scale meteorological models to enhance
    short-term forecasting accuracy. The platform also supports visualization of live weather data,
    forecasts, and atmospheric parameters in a user-friendly and interactive interface.

    Developed by Team Intergalactic Explorers which comprises of Yoginipriya V , Sahana S, Sonika R, Pradeesh Vel Nirmal, Barath R, Shankar this project represents an innovative step toward integrating
    IoT-based environmental sensing and space-based observation for enhanced weather intelligence.
    """)
    
    st.stop()

    st.error("Please enter a valid city name.")
    st.stop()

if lat is None or lon is None:
    st.error(f"❌ Could not find location for city: {city}")
    st.stop()

target_datetime = datetime.datetime.combine(prediction_date, prediction_time)
sample_data = generate_sample_drone_data()

# ------------------ DRONE DATA ------------------
if drone_enabled and drone_data_option != "No Drone Data":
    st.title("🚁 Sample Drone Sensor Data")
    if drone_data_option == "Conditions":
        latest = sample_data.iloc[-1]
        st.markdown("<div style='background-color:rgba(173,216,230,0.3); padding:20px; border-radius:15px;'>", unsafe_allow_html=True)
        st.subheader("Current Drone Sensor Conditions")
        col1, col2 = st.columns(2)
        col1.markdown(f"<div style='font-size:24px; font-weight:bold;'>🌡️ Temperature</div>"
                      f"<div style='font-size:28px; color:#003366;'>{latest['Temperature (°C)']:.2f} °C</div>", unsafe_allow_html=True)
        col2.markdown(f"<div style='font-size:24px; font-weight:bold;'>💧 Humidity</div>"
                      f"<div style='font-size:28px; color:#003366;'>{latest['Humidity (%)']:.2f} %</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    elif drone_data_option == "Data History":
        st.subheader("Drone Data History")
        st.dataframe(sample_data)
        st.line_chart(sample_data.set_index("Timestamp")["Temperature (°C)"])
        st.line_chart(sample_data.set_index("Timestamp")["Humidity (%)"])

# ------------------ NAVIGATOR ------------------
if not drone_enabled or drone_data_option == "No Drone Data":
    if view_option == "Navigator":
        st.title("🌍Drovaan Dashboard")
        now_utc = datetime.datetime.utcnow()
        live_data = get_weather(lat, lon, now_utc)

        # ---- LIVE WEATHER ----
        if live_data:
            live_result = {item["parameter"]: item["coordinates"][0]["dates"][0]["value"] for item in live_data["data"]}
            st.markdown("""
                <div style="background-color:rgba(173,216,230,0.3);
                            padding:8px;border-radius:10px;
                            border:1px solid #87CEFA;
                            box-shadow:0px 0px 10px rgba(135,206,250,0.4);
                            max-width:1200px;
                            margin:auto;">
                <h3 style='color:#003366;'>📍 Live Weather Data</h3>
            """, unsafe_allow_html=True)

            cols = st.columns(3)
            for i, (label, key) in enumerate([("🌡️ Temp", "t_2m:C"), ("💨 Wind", "wind_speed_10m:ms"), ("🌧️ Precip (24h)", "precip_24h:mm")]):
                value = live_result.get(key, "N/A")
                cols[i].markdown(f"<div style='font-size:24px; font-weight:bold;'>{label}</div>"
                                 f"<div style='font-size:28px; color:#003366;'>{value}</div>", unsafe_allow_html=True)

            cols2 = st.columns(3)
            for i, (label, key) in enumerate([("🌤️ UV", "uv:idx"), ("🌅 Sunrise", "sunrise:sql"), ("🌇 Sunset", "sunset:sql")]):
                value = live_result.get(key, "N/A")
                if "sun" in key:
                    value = format_iso_datetime_to_ist(value)
                cols2[i].markdown(f"<div style='font-size:24px; font-weight:bold;'>{label}</div>"
                                  f"<div style='font-size:28px; color:#003366;'>{value}</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
            st.write("---")

        # ---- FORECAST ----
        prediction_data = get_weather(lat, lon, target_datetime)
        if prediction_data:
            pred_result = {item["parameter"]: item["coordinates"][0]["dates"][0]["value"] for item in prediction_data["data"]}
            st.markdown("""
                <div style="background-color:rgba(173,216,230,0.3);
                            padding:8px;border-radius:10px;
                            border:1px solid #87CEFA;
                            box-shadow:0px 0px 10px rgba(135,206,250,0.4);
                            max-width:1200px;
                            margin:auto;">
                <h3 style='color:#003366;'>🤖 Weather Forecast</h3>
            """, unsafe_allow_html=True)

            cols = st.columns(3)
            for i, (label, key) in enumerate([("🌡️ Temp", "t_2m:C"), ("💨 Wind", "wind_speed_10m:ms"), ("🌧️ Precip (24h)", "precip_24h:mm")]):
                value = pred_result.get(key, "N/A")
                cols[i].markdown(f"<div style='font-size:24px; font-weight:bold;'>{label}</div>"
                                 f"<div style='font-size:28px; color:#003366;'>{value}</div>", unsafe_allow_html=True)

            cols2 = st.columns(3)
            for i, (label, key) in enumerate([("🌤️ UV", "uv:idx"), ("🌅 Sunrise", "sunrise:sql"), ("🌇 Sunset", "sunset:sql")]):
                value = pred_result.get(key, "N/A")
                if "sun" in key:
                    value = format_iso_datetime_to_ist(value)
                cols2[i].markdown(f"<div style='font-size:24px; font-weight:bold;'>{label}</div>"
                                  f"<div style='font-size:28px; color:#003366;'>{value}</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # ---- MAP ----
        st.write("---")
        st.subheader("🗺️ City Location Map")
        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))

    # ------------------ ATMOSPHERIC VIEW ------------------
    elif view_option == "Atmospheric view":
        if zoom_level is None:
            zoom_level = 2
        st.title(f"Aerosol Satellite Map - {city} (Zoom {zoom_level})")
        combined_layers = "MODIS_Terra_CorrectedReflectance_TrueColor,Reference_Labels_15m"
        nasa_url = get_nasa_gibs_image_url(lat, lon, zoom_level, combined_layers)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.image(nasa_url, caption="Aerosol Satellite Map with Labels", use_container_width=True)
        with col2:
            st.subheader("City Map")

            st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}))




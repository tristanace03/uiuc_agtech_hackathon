import streamlit as st
import numpy as np
import json
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.colors import ListedColormap
import pandas as pd
import random
# ---------------- Physical constants ----------------

RHO = 1.225
CD = 1.1
AREA = 0.3

# ---------------- Plant geometry ----------------

SHORT_HEIGHT = 1.7 * 0.65
TALL_HEIGHT = 2.81 * 0.65 # correction due to moment arm

# ---------------- Strength distribution ----------------

MEAN_STRENGTH = 150
STD_STRENGTH = 45

# ---------------- Grid size ----------------

N = 400


# -------------------------------------------------------
# Drag force from wind speed
# -------------------------------------------------------

def drag_force(v_mph):

    # convert mph → m/s
    v = v_mph * 0.44704

    # aerodynamic drag equation
    return 0.5 * RHO * CD * AREA * v**2


# -------------------------------------------------------
# Bending moment at plant base
# -------------------------------------------------------

def bending_moment(force, height):

    # moment = force × height
    return force * height


# -------------------------------------------------------
# Convert wind direction to grid movement direction
# -------------------------------------------------------

def is_exposed(i, j, grid, direction):

    deg = float(direction) % 360

    # wind direction = where wind COMES FROM

    if 45 <= deg < 135:      # wind from East
        ui, uj = i, j + 1

    elif 135 <= deg < 225:   # wind from South
        ui, uj = i + 1, j

    elif 225 <= deg < 315:   # wind from West
        ui, uj = i, j - 1

    else:                    # wind from North
        ui, uj = i - 1, j

    # check field boundary
    if ui < 0 or ui >= grid.shape[0] or uj < 0 or uj >= grid.shape[1]:
        return True

    # exposed if upwind plant has fallen
    return not grid[ui, uj]

# -------------------------------------------------------
# Main simulation
# -------------------------------------------------------

def simulate(weather):

    # track plants still standing
    short_alive = np.ones((N, N), dtype=bool)
    tall_alive = np.ones((N, N), dtype=bool)

    # record failure time (index of 15-second timestep)
    short_fall_time = np.full((N, N), -1)
    tall_fall_time = np.full((N, N), -1)

    # assign individual plant strengths
    short_strength = np.random.normal(MEAN_STRENGTH, STD_STRENGTH, (N, N))
    tall_strength = np.random.normal(MEAN_STRENGTH, STD_STRENGTH, (N, N))

    for t, record in enumerate(weather):

        speed = record["wind_speed_10m"]
        gust = record["wind_gusts_10m"]

        # assume worst load between sustained wind and gust
        wind = max(speed, gust)

        direction = record["wind_direction_10m"]

        F = drag_force(wind)

        M_short = bending_moment(F, SHORT_HEIGHT)
        M_tall = bending_moment(F, TALL_HEIGHT)


        for i in range(N):
            for j in range(N):

                # ---------------- Short corn ----------------

                if short_alive[i, j]:

                    if short_alive[i, j]:
                        if is_exposed(i, j, short_alive, direction):
                            if M_short > short_strength[i, j]:
                                short_alive[i, j] = False
                                short_fall_time[i, j] = t

                # ---------------- Tall corn ----------------

                if tall_alive[i, j]:

                    if tall_alive[i, j]:
                        if is_exposed(i, j, tall_alive, direction):
                            if M_tall > tall_strength[i, j]:
                                tall_alive[i, j] = False
                                tall_fall_time[i, j] = t
    return short_alive, tall_alive, short_fall_time, tall_fall_time


# ---------------- Streamlit UI ----------------

st.title("Corn Wind Damage Simulation")


# ---------------- Load ZIP database ----------------

with open("zipcodefile") as f:
    zip_data = json.load(f)

zip_list = [z["zip"] for z in zip_data]

selected_zip = st.selectbox("Select County / Zip Code", zip_list)

selected_year = st.selectbox(
    "Select Year",
    list(range(2015, 2026))
)


# ---------------- Lookup coordinates ----------------

zip_entry = next(z for z in zip_data if z["zip"] == selected_zip)

lat = zip_entry["lat"]
lon = zip_entry["long"]


# ---------------- Session state ----------------

if "weather_loaded" not in st.session_state:
    st.session_state.weather_loaded = False


# ---------------- Fetch weather ----------------

from wind_data import call

if st.button("Load Weather Data"):

    with st.spinner("Fetching weather data..."):

        call.fetch_weather(
            latitude=lat,
            longitude=lon,
            year=selected_year
        )

    st.session_state.weather_loaded = True

    st.success("Weather data loaded")


# ---------------- Block until weather exists ----------------

weather_path = Path("wind_data/latest_weather.json")

if not st.session_state.weather_loaded or not weather_path.exists():
    st.info("Load weather data to enable simulation.")
    st.stop()


# ---------------- Load weather ----------------

with open(weather_path) as f:
    weather = json.load(f)

weather_df = pd.DataFrame(weather)

weather_df["date"] = pd.to_datetime(weather_df["date"])

weather_df["day"] = weather_df["date"].dt.date


# ---------------- Find worst 3 wind days ----------------

daily_gust = weather_df.groupby("day")["wind_gusts_10m"].max()

worst_days = daily_gust.nlargest(3)


st.subheader("Top 3 Wind Days During Near-Harvest")

for i, (day, gust) in enumerate(worst_days.items(), start=1):

    st.write(f"**Storm {i}** — {day} (Max Gust: {gust:.1f} mph)")


# ---------------- Simulation buttons ----------------

st.subheader("Run Simulation")


for i, (day, gust) in enumerate(worst_days.items(), start=1):

    if st.button(f"Simulate Storm {i} ({day})"):

        day_data = weather_df[weather_df["day"] == day]

        weather_records = day_data.to_dict(orient="records")

        short_grid, tall_grid, short_time, tall_time = simulate(weather_records)

        short_remaining = np.sum(short_grid)
        tall_remaining = np.sum(tall_grid)

        st.subheader(f"Results for {day}")

        col1, col2 = st.columns(2)

        col1.metric("Short Corn Remaining", short_remaining)
        col2.metric("Tall Corn Remaining", tall_remaining)


        # ---------------- Plot grids ----------------

        corn_cmap = ListedColormap(["black", "green"])

        col1, col2 = st.columns(2)

        with col1:

            st.subheader("Short Corn")

            fig1, ax1 = plt.subplots()

            ax1.imshow(short_grid.astype(int), cmap=corn_cmap, vmin=0, vmax=1)

            ax1.axis("off")

            st.pyplot(fig1)

        with col2:

            st.subheader("Tall Corn")

            fig2, ax2 = plt.subplots()

            ax2.imshow(tall_grid.astype(int), cmap=corn_cmap, vmin=0, vmax=1)

            ax2.axis("off")

            st.pyplot(fig2)
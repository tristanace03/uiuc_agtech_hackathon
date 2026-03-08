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
AREA = 0.18

# ---------------- Plant geometry ----------------

SHORT_HEIGHT = 1.7
TALL_HEIGHT = 2.2

# ---------------- Strength distribution ----------------

MEAN_STRENGTH = 150
STD_STRENGTH = 15

# ---------------- Grid size ----------------

N = 90


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

    # convert wind direction to grid offset
    deg = float(direction) % 360

    if 45 <= deg < 135:
        di, dj = (0, -1)      # ~east
    elif 135 <= deg < 225:
        di, dj = (-1, 0)      # ~south
    elif 225 <= deg < 315:
        di, dj = (0, 1)     # ~west
    else:
        di, dj = (1, 0)     # ~north

    # location of the plant upwind
    ui = i - di
    uj = j - dj

    # if upwind position is outside field → plant is on windward edge
    if ui < 0 or ui >= N or uj < 0 or uj >= N:
        return True

    # plant becomes exposed if the upwind neighbor has fallen
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

                    if is_exposed(i, j, short_alive, direction):
                        if M_short > short_strength[i, j]:
                            short_alive[i, j] = False
                            short_fall_time[i, j] = t

                # ---------------- Tall corn ----------------

                if tall_alive[i, j]:

                    if is_exposed(i, j, tall_alive, direction):
                        if M_tall > tall_strength[i, j]:
                            tall_alive[i, j] = False
                            tall_fall_time[i, j] = t
    return short_alive, tall_alive, short_fall_time, tall_fall_time


from wind_data import call

import streamlit as st
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.colors import ListedColormap

from wind_data import call


arr_short = []
arr_tall = []
# ---------------- Page config ----------------

st.set_page_config(page_title="Short Corn vs Tall Corn Lodging")

st.title("Short Corn vs Tall Corn Lodging")


# ---------------- Load ZIP database ----------------

with open("zipcodefile") as f:
    zip_data = json.load(f)

zip_list = [z["zip"] for z in zip_data]


# ---------------- Sidebar controls ----------------

st.sidebar.header("Simulation Settings")

selected_zip = st.sidebar.selectbox(
    "Select County / Zip Code",
    zip_list,
    key="zip_selector"
)

start_year = st.sidebar.selectbox(
    "Start Year",
    list(range(2015, 2026)),
    index=0,
    key="start_year_selector"
)

end_year = st.sidebar.selectbox(
    "End Year",
    list(range(2015, 2026)),
    index=10,
    key="end_year_selector"
)


# ---------------- Validate range ----------------

if start_year > end_year:
    st.error("Start year must be before end year.")
    st.stop()


# ---------------- Lookup coordinates ----------------

zip_entry = next(z for z in zip_data if z["zip"] == selected_zip)

lat = zip_entry["lat"]
lon = zip_entry["long"]


# ---------------- Fetch weather (cached) ----------------

@st.cache_data
def fetch_weather_cached(latitude, longitude, year_start, year_end):

    call.fetch_weather(
        latitude=latitude,
        longitude=longitude,
        year_start=year_start,
        year_end=year_end
    )

    weather_path = Path("wind_data/latest_weather.json")

    with open(weather_path) as f:
        weather = json.load(f)

    return weather


with st.spinner("Fetching weather data..."):
    weather = fetch_weather_cached(lat, lon, start_year, end_year)

st.success(f"Weather data loaded ({start_year}–{end_year})")


# ---------------- Load weather dataframe ----------------

weather_df = pd.DataFrame(weather)

weather_df["date"] = pd.to_datetime(weather_df["date"])
weather_df["day"] = weather_df["date"].dt.date


# ---------------- Find worst wind days ----------------

daily_gust = weather_df.groupby("day")["wind_gusts_10m"].max()

worst_days = daily_gust.nlargest(3)

st.subheader("Top 3 Wind Days")

for i, (day, gust) in enumerate(worst_days.items(), start=1):

    st.write(f"**Storm {i}** — {day} (Max Gust: {gust:.1f} mph)")


# ---------------- Run simulations automatically ----------------

st.subheader("Simulation Results")

corn_cmap = ListedColormap(["black", "green"])


for i, (day, gust) in enumerate(worst_days.items(), start=1):

    day_data = weather_df[weather_df["day"] == day]

    weather_records = day_data.to_dict(orient="records")

    short_grid, tall_grid, short_time, tall_time = simulate(weather_records)

    short_remaining = np.sum(short_grid)
    arr_short.append(short_remaining)
    tall_remaining = np.sum(tall_grid)
    arr_tall.append(tall_remaining)
    st.subheader(f"Storm {i} Results — {day}")

    col1, col2 = st.columns(2)

    col1.metric("Short Corn Remaining", short_remaining)
    col2.metric("Tall Corn Remaining", tall_remaining)


    # ---------------- Plot grids ----------------

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
    # ---------------- Average results across storms ----------------

    if len(arr_short) > 0:

        avg_short_remaining = sum(arr_short) / len(arr_short)
        avg_tall_remaining = sum(arr_tall) / len(arr_tall)

        st.subheader("Average Remaining Corn Across Storms")

        col1, col2 = st.columns(2)

        col1.metric(
            "Average Short Corn Remaining",
            f"{avg_short_remaining:.1f}"
        )

        col2.metric(
            "Average Tall Corn Remaining",
            f"{avg_tall_remaining:.1f}"
        )
    # ---------------- Average results across storms ----------------

if len(arr_short) > 0:

    avg_short_remaining = sum(arr_short) / len(arr_short)
    avg_tall_remaining = sum(arr_tall) / len(arr_tall)

    st.subheader("Average Remaining Corn Across Storms")

    col1, col2 = st.columns(2)
    ret_short = (8100 - avg_short_remaining)/8100
    ret_tall = (8100 - avg_tall_remaining)/8100
    col1.metric(
        "Short Corn Lost",
        f"{ret_short:.5f}"
    )

    col2.metric(
        "Proportion Tall Corn Lost",
        f"{ret_tall:.5f}"
        )
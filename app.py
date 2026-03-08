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

    if 22.5 <= deg < 67.5:
        di, dj = (1, -1)       # northeast
    elif 67.5 <= deg < 112.5:
        di, dj = (0, -1)       # east
    elif 112.5 <= deg < 157.5:
        di, dj = (-1, -1)      # southeast
    elif 157.5 <= deg < 202.5:
        di, dj = (-1, 0)       # south
    elif 202.5 <= deg < 247.5:
        di, dj = (-1, 1)       # southwest
    elif 247.5 <= deg < 292.5:
        di, dj = (0, 1)        # west
    elif 292.5 <= deg < 337.5:
        di, dj = (1, 1)        # northwest
    else:
        di, dj = (1, 0)        # north
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

    # record failure time
    short_fall_time = np.full((N, N), -1)
    tall_fall_time = np.full((N, N), -1)

    # assign individual plant strengths
    short_strength = np.random.normal(MEAN_STRENGTH, STD_STRENGTH, (N, N))
    tall_strength = np.random.normal(MEAN_STRENGTH, STD_STRENGTH, (N, N))

    for t, record in enumerate(weather):

        speed = record["wind_speed_10m"]
        gust = record["wind_gusts_10m"]

        wind = max(speed, gust)
        direction = record["wind_direction_10m"]

        F = drag_force(wind)

        M_short = bending_moment(F, SHORT_HEIGHT)
        M_tall = bending_moment(F, TALL_HEIGHT)

        # store plants that should fall this timestep
        short_to_fall = []
        tall_to_fall = []

        for i in range(N):
            for j in range(N):

                # ---------------- Short corn ----------------
                if short_alive[i, j]:

                    if is_exposed(i, j, short_alive, direction):
                        if M_short > short_strength[i, j]:
                            short_to_fall.append((i, j))

                # ---------------- Tall corn ----------------
                if tall_alive[i, j]:

                    if is_exposed(i, j, tall_alive, direction):
                        if M_tall > tall_strength[i, j]:
                            tall_to_fall.append((i, j))

        # apply failures AFTER evaluating the whole grid
        for i, j in short_to_fall:
            short_alive[i, j] = False
            short_fall_time[i, j] = t

        for i, j in tall_to_fall:
            tall_alive[i, j] = False
            tall_fall_time[i, j] = t

    return short_alive, tall_alive, short_fall_time, tall_fall_time
from wind_data import call


from wind_data import call


arr_short = []
arr_tall = []
# ---------------- Page config ----------------
# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------

st.set_page_config(page_title="Short Corn vs Tall Corn Lodging")

st.title("Short Corn vs Tall Corn Lodging Simulator")

st.info("""
This simulator models corn lodging using historical wind storms.

• Each square = one plant  
• Green = standing corn  
• Black = lodged corn  
• Based on historical wind gust data
""")


# -------------------------------------------------------
# LOAD ZIP DATABASE
# -------------------------------------------------------

with open("zipcodefile") as f:
    zip_data = json.load(f)

zip_list = [z["zip"] for z in zip_data]


# -------------------------------------------------------
# SIDEBAR CONTROLS
# -------------------------------------------------------

st.sidebar.header("Simulation Settings")

selected_zip = st.sidebar.selectbox(
    "Zip Code",
    zip_list
)

start_year = st.sidebar.selectbox(
    "Start Year",
    list(range(2015, 2026)),
    index=0
)

end_year = st.sidebar.selectbox(
    "End Year",
    list(range(2015, 2026)),
    index=10
)

if start_year > end_year:
    st.error("Start year must be before end year.")
    st.stop()


# -------------------------------------------------------
# LOOKUP COORDINATES
# -------------------------------------------------------

zip_entry = next(z for z in zip_data if z["zip"] == selected_zip)

lat = zip_entry["lat"]
lon = zip_entry["long"]


# -------------------------------------------------------
# FETCH WEATHER
# -------------------------------------------------------

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


# -------------------------------------------------------
# WEATHER DATAFRAME
# -------------------------------------------------------

weather_df = pd.DataFrame(weather)

weather_df["date"] = pd.to_datetime(weather_df["date"])
weather_df["day"] = weather_df["date"].dt.date


# -------------------------------------------------------
# WORST STORMS
# -------------------------------------------------------

st.header("Strongest Storms")

st.info("""
This model simulates corn lodging during severe wind events using a simplified physics-based plant failure model. 
The field is represented as a grid of individual plants (~8100 plants ≈ 4.5 acres), each assigned a random structural strength to represent natural variation in stalk rigidity. 
Wind speed and gust data from historical storms are converted into aerodynamic drag forces, which generate a bending moment at the base of each plant proportional to plant height. 
A plant lodges when the wind-induced bending moment exceeds its structural strength threshold. 
Plants also shield their downwind neighbors, so when one plant falls it increases exposure and can trigger cascading lodging across the field. 
Final yield and profit are estimated from the number of plants remaining upright after the storm using assumed yields, seed costs, and corn price.
""")

daily_gust = weather_df.groupby("day")["wind_gusts_10m"].max()

worst_days = daily_gust.nlargest(3)

for i, (day, gust) in enumerate(worst_days.items(), start=1):
    st.write(f"Storm {i} — {day} (Max Gust: {gust:.1f} mph)")


# -------------------------------------------------------
# RUN SIMULATIONS
# -------------------------------------------------------

st.header("Storm Simulations")

corn_cmap = ListedColormap(["black", "green"])

arr_short = []
arr_tall = []

for i, (day, gust) in enumerate(worst_days.items(), start=1):

    st.divider()
    st.subheader(f"Storm {i}: {day}")

    day_data = weather_df[weather_df["day"] == day]

    weather_records = day_data.to_dict(orient="records")

    short_grid, tall_grid, short_time, tall_time = simulate(weather_records)

    short_remaining = np.sum(short_grid)
    tall_remaining = np.sum(tall_grid)

    arr_short.append(short_remaining)
    arr_tall.append(tall_remaining)

    c1, c2, c3 = st.columns(3)

    c1.metric("Max Gust", f"{gust:.1f} mph")
    c2.metric("Short Corn Standing", short_remaining)
    c3.metric("Tall Corn Standing", tall_remaining)

    col1, col2 = st.columns(2)

    with col1:

        st.caption("Short Corn Survival Map")

        fig1, ax1 = plt.subplots()
        ax1.imshow(short_grid.astype(int), cmap=corn_cmap, vmin=0, vmax=1)
        ax1.axis("off")
        st.pyplot(fig1)

    with col2:

        st.caption("Tall Corn Survival Map")

        fig2, ax2 = plt.subplots()
        ax2.imshow(tall_grid.astype(int), cmap=corn_cmap, vmin=0, vmax=1)
        ax2.axis("off")
        st.pyplot(fig2)


# -------------------------------------------------------
# LODGING SUMMARY
# -------------------------------------------------------

st.header("Average Lodging Results")

avg_short_remaining = sum(arr_short) / len(arr_short)
avg_tall_remaining = sum(arr_tall) / len(arr_tall)

ret_short = (8100 - avg_short_remaining) / 8100
ret_tall = (8100 - avg_tall_remaining) / 8100

col1, col2 = st.columns(2)

col1.metric(
    "Short Corn Lodging Rate",
    f"{ret_short:.2%}"
)

col2.metric(
    "Tall Corn Lodging Rate",
    f"{ret_tall:.2%}"
)


# -------------------------------------------------------
# ECONOMIC MODEL
# -------------------------------------------------------

st.header("Economic Outcome")

corn_price = 4.50
plants_per_acre = 34000

yield_tall_per_plant = 220 / plants_per_acre
yield_short_per_plant = 210 / plants_per_acre

seeds_per_bag = 80000
bag_price_tall = 280
bag_price_short = 310

seed_cost_per_seed_tall = bag_price_tall / seeds_per_bag
seed_cost_per_seed_short = bag_price_short / seeds_per_bag

rev_tall_per_plant = yield_tall_per_plant * corn_price
rev_short_per_plant = yield_short_per_plant * corn_price

revenue_tall = avg_tall_remaining * rev_tall_per_plant
revenue_short = avg_short_remaining * rev_short_per_plant

seed_cost_tall = 8100 * seed_cost_per_seed_tall
seed_cost_short = 8100 * seed_cost_per_seed_short

profit_tall = revenue_tall - seed_cost_tall
profit_short = revenue_short - seed_cost_short

col1, col2 = st.columns(2)

col1.metric("Tall Corn Profit", f"${profit_tall:.2f}")
col2.metric("Short Corn Profit", f"${profit_short:.2f}")

profit_diff = profit_short - profit_tall

st.metric(
    "Profit Difference (Short − Tall)",
    f"${profit_diff:.2f}"
)


# -------------------------------------------------------
# RECOMMENDATION
# -------------------------------------------------------

st.header("Planting Recommendation")

if profit_short > profit_tall:

    st.success(
        "SHORT corn is more profitable under historical wind conditions."
    )

else:

    st.success(
        "TALL corn produces higher profit despite lodging risk."
    )
st.divider()

st.markdown("""
**Sources**
Bayer PRECEON™ Smart Corn System  
https://www.bayer.com/en/agriculture/preceon-smart-corn-system

Tall and Short Stature Corn Agronomic Response to Nitrogen Rates – Crop Science  
https://acsess.onlinelibrary.wiley.com/doi/10.1002/csc2.20702

""")
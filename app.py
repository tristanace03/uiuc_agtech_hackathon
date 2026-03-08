import streamlit as st
import numpy as np
import json
import random
import matplotlib.pyplot as plt
from pathlib import Path

# physical constants
RHO = 1.225
CD = 1.1
AREA = 0.18

# plant properties
SHORT_HEIGHT = 1.7
TALL_HEIGHT = 2.81

SHORT_STRENGTH = 55
TALL_STRENGTH = 70

# damage sensitivity constant
K_DAMAGE = 0.7

# grid size
N = 30


# drag force from wind
def drag_force(v_mph):
    v = v_mph * 0.44704
    return 0.5 * RHO * CD * AREA * v**2


# bending moment
def bending_moment(force, height):
    return force * height


# hourly failure probability
def hourly_failure_probability(moment, strength):
    load_ratio = moment / strength
    damage = max(0, load_ratio - 1)
    return 1 - np.exp(-K_DAMAGE * damage)


# wind direction → neighbor
def wind_offset(direction):
    deg = float(direction) % 360

    # convert FROM direction to TO direction
    deg = (deg + 0) % 360

    if 45 <= deg < 135:
        return (0, 1)      # east
    elif 135 <= deg < 225:
        return (1, 0)      # south
    elif 225 <= deg < 315:
        return (0, -1)     # west
    else:
        return (-1, 0)     # north


# windward edge cells
def windward_edge(di, dj):

    if di == -1:
        return [(0, j) for j in range(N)]
    if di == 1:
        return [(N - 1, j) for j in range(N)]
    if dj == -1:
        return [(i, 0) for i in range(N)]
    if dj == 1:
        return [(i, N - 1) for i in range(N)]


# main simulation
def simulate(weather):

    short_alive = np.ones((N, N), dtype=bool)
    tall_alive = np.ones((N, N), dtype=bool)

    short_fall_time = np.full((N, N), -1)
    tall_fall_time = np.full((N, N), -1)

    for t, record in enumerate(weather):

        speed = record["wind_speed_10m"]
        gust = record["wind_gusts_10m"]
        wind = max(speed, gust)

        direction = record["wind_direction_10m"]

        F = drag_force(wind)

        M_short = bending_moment(F, SHORT_HEIGHT)
        M_tall = bending_moment(F, TALL_HEIGHT)

        p_short = hourly_failure_probability(M_short, SHORT_STRENGTH)
        p_tall = hourly_failure_probability(M_tall, TALL_STRENGTH)

        di, dj = wind_offset(direction)

        # seed windward edge
        for i, j in windward_edge(di, dj):
            if short_alive[i, j] and random.random() < p_short:
                short_alive[i, j] = False
                short_fall_time[i, j] = t
                break

        for i, j in windward_edge(di, dj):
            if tall_alive[i, j] and random.random() < p_tall:
                tall_alive[i, j] = False
                tall_fall_time[i, j] = t
                break

        candidates_short = []
        candidates_tall = []

        for i in range(N):
            for j in range(N):

                ni = i + di
                nj = j + dj

                if 0 <= ni < N and 0 <= nj < N:

                    if short_alive[i, j] and not short_alive[ni, nj]:
                        candidates_short.append((i, j))

                    if tall_alive[i, j] and not tall_alive[ni, nj]:
                        candidates_tall.append((i, j))

        random.shuffle(candidates_short)
        random.shuffle(candidates_tall)

        for i, j in candidates_short:
            if random.random() < p_short:
                short_alive[i, j] = False
                short_fall_time[i, j] = t
                break

        for i, j in candidates_tall:
            if random.random() < p_tall:
                tall_alive[i, j] = False
                tall_fall_time[i, j] = t
                break

    return short_alive, tall_alive, short_fall_time, tall_fall_time


# ---------------- Streamlit UI ----------------

st.title("Corn Wind Damage Simulation")

weather_path = Path("wind_data/latest_weather.json")

if not weather_path.exists():
    st.error("Weather file not found: wind_data/latest_weather.json")
    st.stop()

with open(weather_path) as f:
    weather = json.load(f)

st.write(f"Weather records loaded: {len(weather)} hours")

if st.button("Run Simulation"):

    short_grid, tall_grid, short_time, tall_time = simulate(weather)

    short_remaining = np.sum(short_grid)
    tall_remaining = np.sum(tall_grid)

    col1, col2 = st.columns(2)

    col1.metric("Short Corn Remaining", short_remaining)
    col2.metric("Tall Corn Remaining", tall_remaining)

    st.subheader("Short Corn Grid")

    fig1, ax1 = plt.subplots()
    ax1.imshow(short_grid.astype(int))
    ax1.set_title("Short Corn Alive (1=alive,0=fallen)")
    ax1.axis("off")
    st.pyplot(fig1)

    st.subheader("Tall Corn Grid")

    fig2, ax2 = plt.subplots()
    ax2.imshow(tall_grid.astype(int))
    ax2.set_title("Tall Corn Alive (1=alive,0=fallen)")
    ax2.axis("off")
    st.pyplot(fig2)
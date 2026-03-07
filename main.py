import numpy as np
import json

# physical constants

rho = 1.225          # air density kg/m^3
Cd = 1.1             # canopy drag coefficient
A = 0.08             # effective frontal area per plant (m^2)

alpha = 1.14         # exponent from paper

canopy_wind_factor = 0.7   # wind reduction inside crop canopy

# plant properties 
short_corn = 1.7
tall_corn = 2.81

# DARLING-style bending strengths (N*m)
S_short = 220
S_tall = 220


# physics helpers
def mph_to_ms(v_mph):
    return v_mph * 0.44704


def wind_force(v_mph):
    """
    Drag force from wind
    """
    v = mph_to_ms(v_mph)
    return 0.5 * rho * Cd * A * v**2


def wind_moment(v_mph, height):
    """
    Convert wind force to bending moment.
    Center of pressure assumed ~0.6h
    """
    F = wind_force(v_mph)
    return F * (0.6 * height)


def safety_factor(v_mph, height, strength):
    """
    SF = resistance / applied moment
    """
    M = wind_moment(v_mph, height)

    resistance = strength * height**(-alpha)

    if M == 0:
        return np.inf

    return resistance / M


# probabilistic failure

def snap_probability(sf, k=4):
    """
    Logistic failure curve centered at SF=1
    """
    x = np.clip(1 - sf, -50, 50)
    return 1 / (1 + np.exp(-k * x))


def plant_snaps(v_mph, height, strength):
    sf = safety_factor(v_mph, height, strength)
    p = snap_probability(sf)

    return np.random.rand() < p, sf, p


# simulation

def simulate(debug=True):

    with open("wind_data/latest_weather.json") as f:
        weather = json.load(f)

    short_alive = True
    tall_alive = True

    short_time = None
    tall_time = None

    for i, record in enumerate(weather):

        wind = max(record["wind_gusts_10m"], 0)

        # canopy reduction since we measure at 10 meters but the crop is well lower
        wind *= canopy_wind_factor

        if debug and i < 20:
            print("\n--- timestep", i, "---")
            print("raw wind:", record["wind_gusts_10m"], "mph")
            print("canopy wind:", wind, "mph")

        # short corn
        if short_alive:

            snapped, sf, p = plant_snaps(wind, short_corn, S_short)

            if debug and i < 20:
                print("short SF:", round(sf,3), "prob:", round(p,3))

            if snapped:
                short_alive = False
                short_time = i

                if debug:
                    print("SHORT CORN SNAPPED")

        # tall corn
        if tall_alive:

            snapped, sf, p = plant_snaps(wind, tall_corn, S_tall)

            if debug and i < 20:
                print("tall SF:", round(sf,3), "prob:", round(p,3))

            if snapped:
                tall_alive = False
                tall_time = i

                if debug:
                    print("TALL CORN SNAPPED")

    return short_alive, tall_alive, short_time, tall_time


# run

short_alive, tall_alive, short_time, tall_time = simulate()

print("\n=========================")
print("RESULTS")
print("=========================")

print("Short corn survived:", short_alive)
print("Tall corn survived:", tall_alive)

if short_time is not None:
    print("Short corn snapped at timestep:", short_time)

if tall_time is not None:
    print("Tall corn snapped at timestep:", tall_time)
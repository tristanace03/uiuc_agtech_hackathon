import numpy as np

rho = 1.225
Cd = 0.35
A = 0.5

alpha = 1.14


short_corn = 1.7  # meters
# Source: Tollenaar & Lee (2002), Field Crops Research

tall_corn = 2.81  # meters
# Source: Tollenaar et al., Field Crops Research studies on maize architecture

S_short = 120
S_tall = 120

def mph_to_ms(v_mph):
    return v_mph * 0.44704

def wind_force(v_mph):

    v = mph_to_ms(v_mph)

    return 0.5 * Cd * rho * A * v**2

def bending_moment(v_mph, height):

    F = wind_force(v_mph)

    return F * height

def lodging_resistance(strength, height):
    return strength * height**(-alpha)


def lodging_risk(v_mph, height, strength):

    M = bending_moment(v_mph, height)

    R = lodging_resistance(strength, height)

    return M / R


def lodging_probability(risk, k=5):
    # purely a modeling choice
    return 1 / (1 + np.exp(-k*(risk-1)))

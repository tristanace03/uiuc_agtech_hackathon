import numpy as np
from phy import mph_to_ms, wind_force, bending_moment, lodging_resistance, lodging_risk, lodging_probability

rho = 1.225 # https://www.sciencedirect.com/science/article/pii/S0378429023002010
Cd = 0.35
A = 0.5

alpha = 1.14


short_corn = 1.7  # meters
# Source: Tollenaar & Lee (2002), Field Crops Research

tall_corn = 2.81  # meters
# Source: Tollenaar et al., Field Crops Research studies on maize architecture

S_short = 120
S_tall = 120



def simulate(n_events=1):

    short_falls = 0
    tall_falls = 0

    for _ in range(n_events):

        # sample wind gust
        wind = np.random.normal(25, 10)

        wind = max(wind,0)

        risk_s = lodging_risk(wind, short_corn, S_short)
        risk_t = lodging_risk(wind, tall_corn, S_tall)

        p_s = lodging_probability(risk_s)
        p_t = lodging_probability(risk_t)

        if np.random.rand() < p_s: # we are simulating 
            short_falls += 1

        if np.random.rand() < p_t:
            tall_falls += 1

    return short_falls/n_events, tall_falls/n_events


short_prob, tall_prob = simulate()

print("Short corn lodging probability:", short_prob)
print("Tall corn lodging probability:", tall_prob)
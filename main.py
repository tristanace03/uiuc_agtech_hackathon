import numpy as np  
import scipy

# let short corn be 5 ft. tall, as a constant
# let tall corn be 7 ft. tall, as a constant

short_corn = 1.7 # https://www.researchgate.net/publication/223831105_Tollenaar_M_Lee_E_A_Yield_potential_yield_stability_and_stress_tolerance_in_maize_Field_Crop_Res_2002
tall_corn = 2.81 # https://www.sciencedirect.com/science/article/pii/S0378429002001247

# the force of wind
f = lambda x: x

# integrate force of wind by height (should be ds)
# scipy.integrate.quad returns a tuple with (res, precision)
s_total = scipy.integrate.quad(f, 0, short_corn)[0]
t_total = scipy.integrate.quad(f, 0, tall_corn)[0]

# arbitrary constants that depend on agregate of soil, identity of plant, etc
root_sys_s = 1 
root_sys_t = 1.5 

s = s / root_sys_s
t = t / root_sys_t

print(s_total, t_total)

# assume there is a function of wind, given break points, can estimate

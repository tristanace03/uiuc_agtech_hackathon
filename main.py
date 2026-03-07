import numpy as np  
import scipy

# let short corn be 5 ft. tall, as a constant
# let tall corn be 7 ft. tall, as a constant

s = 5
t = 7

# the force of wind
f = lambda x: x

# integrate force of wind by height (should be ds)
s_total = scipy.integrate.quad(f, 0, s)[0]
t_total = scipy.integrate.quad(f, 0, t)[0]

# arbitrary constants that depend on agregate of soil, identity of plant, etc
root_sys_s = 1 
root_sys_t = 1.5 

s = s / root_sys_s
t = t / root_sys_t

print(s_total, t_total)

# assume there is a function of wind, given break points, can estimate

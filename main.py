import numpy as np

c = np.array([10,10,10,10,10,10,10])

x = np.array([0.1,0.3,0.3,0.7,0.6,0.5,0.1])

ctx = c.T @ x


print(ctx)
print(ctx > 50)
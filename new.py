import json
import matplotlib.pyplot as plt

with open("wind_data/latest_weather.json") as f:
    data = json.load(f)

# use only first 100 entries
data = data

directions = [d for d in data]

bins = ["N","NE","E","SE","S","SW","W","NW"]
counts = [0]*8

for d in directions:
    idx = int(((d["wind_direction_10m"] + 22.5) % 360) // 45)
    if (d["wind_gusts_10m"] > 40):
        counts[idx] += 1

plt.figure()
plt.bar(bins, counts)

plt.xlabel("Wind Direction")
plt.ylabel("Frequency (first 100 samples)")
plt.title("Wind Direction Distribution")

plt.tight_layout()
plt.show()
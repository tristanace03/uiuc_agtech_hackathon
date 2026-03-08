# Corn Lodging Wind Simulator

A physics-based simulation that models corn lodging under historical wind storms and compares the economic performance of short vs tall corn hybrids.

The model uses historical wind data, aerodynamic wind loading, and stochastic plant strength to simulate how wind events propagate lodging across a field.

------------------------------------------------------------

OVERVIEW

This simulator represents a corn field as a grid of individual plants (~8100 plants ≈ 4.5 acres).  
Each plant is assigned a random structural strength to represent natural variation in stalk rigidity.

Historical wind data (speed, gusts, and direction) are converted into aerodynamic drag forces, which produce a bending moment at the base of each plant.

A plant lodges when the wind-induced bending moment exceeds its structural strength threshold.

Plants also shield downwind neighbors, so when one plant falls it exposes others, allowing lodging to cascade through the field.

After storms are simulated, surviving plants are converted to yield and profit estimates using assumed yields, seed costs, and corn price.

------------------------------------------------------------

FEATURES

• Historical wind data by ZIP code  
• Physics-based drag and bending calculations  
• Spatial plant shielding and cascading lodging  
• Comparison of short vs tall corn hybrids  
• Visualization of plant survival across the field  
• Economic outcome estimation  

------------------------------------------------------------

REQUIREMENTS

Python 3.9+

Install dependencies with:

pip install -r requirements.txt

------------------------------------------------------------

RUNNING THE APP

Start the simulator with:

streamlit run app.py

The app will automatically open in your browser.

------------------------------------------------------------

PROJECT STRUCTURE

.
├── app.py
├── requirements.txt
├── zipcodefile
├── wind_data/
│   ├── call.py
│   └── latest_weather.json

------------------------------------------------------------

MODEL ASSUMPTIONS

• Each grid cell represents one corn plant  
• Plant strength follows a normal distribution  
• Wind force is calculated using the aerodynamic drag equation  
• Bending moment is proportional to plant height  
• Plants shield neighbors from wind exposure  
• Lodged plants remain down for the rest of the storm  
• Yield is proportional to surviving plants  

The model is designed to compare relative hybrid performance under wind risk rather than perfectly predict real field outcomes.

------------------------------------------------------------

LICENSE

MIT License

import numpy as np
import pandas as pd

np.random.seed(42)

rows = 1000

# Simulate normal motor behavior
temperature = np.random.normal(loc=55, scale=2.5, size=rows)
humidity = np.random.normal(loc=50, scale=5, size=rows)
gas = np.random.normal(loc=120, scale=10, size=rows)
current = np.random.normal(loc=4.5, scale=0.4, size=rows)
vibration = np.random.normal(loc=0.35, scale=0.07, size=rows)

# Clip values to realistic ranges
temperature = np.clip(temperature, 48, 62)
humidity = np.clip(humidity, 35, 65)
gas = np.clip(gas, 90, 150)
current = np.clip(current, 3.8, 5.8)
vibration = np.clip(vibration, 0.18, 0.55)

# Create DataFrame
data = pd.DataFrame({
    "temperature": temperature,
    "humidity": humidity,
    "gas": gas,
    "current": current,
    "vibration": vibration
})

# Save dataset
data.to_csv("motor_normal_data.csv", index=False)

print("Synthetic motor dataset generated successfully!")
print(data.head())

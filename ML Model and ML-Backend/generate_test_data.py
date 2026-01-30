import numpy as np
import pandas as pd

np.random.seed(99)  # New seed for test data

rows = 500  # Number of test samples

# --- 1. Generate Normal Data (Similar to Training) ---
# Normal ranges: Temp ~55, Hum ~50, Gas ~120, Curr ~4.5, Vib ~0.35
temp_norm = np.random.normal(loc=55, scale=2.5, size=rows)
hum_norm = np.random.normal(loc=50, scale=5, size=rows)
gas_norm = np.random.normal(loc=120, scale=10, size=rows)
curr_norm = np.random.normal(loc=4.5, scale=0.4, size=rows)
vib_norm = np.random.normal(loc=0.35, scale=0.07, size=rows)

# Labels: 0 = Normal
labels_norm = np.zeros(rows)

# --- 2. Generate Anomalous Data ---
anom_rows = 100

# Anomaly 1: Overheating (High Temp)
temp_anom1 = np.random.uniform(75, 95, anom_rows)
# Other features normal
hum_anom1 = np.random.normal(loc=50, scale=5, size=anom_rows)
gas_anom1 = np.random.normal(loc=120, scale=10, size=anom_rows)
curr_anom1 = np.random.normal(loc=4.5, scale=0.4, size=anom_rows)
vib_anom1 = np.random.normal(loc=0.35, scale=0.07, size=anom_rows)

# Anomaly 2: Mechanical Fault (High Vibration)
vib_anom2 = np.random.uniform(0.7, 1.2, anom_rows)
# Other features normal
temp_anom2 = np.random.normal(loc=55, scale=2.5, size=anom_rows)
hum_anom2 = np.random.normal(loc=50, scale=5, size=anom_rows)
gas_anom2 = np.random.normal(loc=120, scale=10, size=anom_rows)
curr_anom2 = np.random.normal(loc=4.5, scale=0.4, size=anom_rows)

# Anomaly 3: Electrical Fault (High Current)
curr_anom3 = np.random.uniform(7.0, 9.0, anom_rows)
# Other features normal
temp_anom3 = np.random.normal(loc=55, scale=2.5, size=anom_rows)
hum_anom3 = np.random.normal(loc=50, scale=5, size=anom_rows)
gas_anom3 = np.random.normal(loc=120, scale=10, size=anom_rows)
vib_anom3 = np.random.normal(loc=0.35, scale=0.07, size=anom_rows)

# Labels: 1 = Anomaly
labels_anom = np.ones(anom_rows * 3)

# Combine Anomalies
temp_anom = np.concatenate([temp_anom1, temp_anom2, temp_anom3])
hum_anom = np.concatenate([hum_anom1, hum_anom2, hum_anom3])
gas_anom = np.concatenate([gas_anom1, gas_anom2, gas_anom3])
curr_anom = np.concatenate([curr_anom1, curr_anom2, curr_anom3])
vib_anom = np.concatenate([vib_anom1, vib_anom2, vib_anom3])

# --- 3. Combine All Data ---
temperature = np.concatenate([temp_norm, temp_anom])
humidity = np.concatenate([hum_norm, hum_anom])
gas = np.concatenate([gas_norm, gas_anom])
current = np.concatenate([curr_norm, curr_anom])
vibration = np.concatenate([vib_norm, vib_anom])
labels = np.concatenate([labels_norm, labels_anom])

# Create DataFrame
data = pd.DataFrame({
    "temperature": temperature,
    "humidity": humidity,
    "gas": gas,
    "current": current,
    "vibration": vibration,
    "is_anomaly": labels
})

# Save dataset
data.to_csv("motor_test_data.csv", index=False)

print(f"Test dataset generated: {len(data)} samples")
print(f"Normal samples: {rows}")
print(f"Anomalous samples: {len(labels_anom)}")
print(data.head())
print(data.tail())

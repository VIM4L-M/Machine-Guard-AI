
import requests
import json
import joblib
import pandas as pd
import numpy as np
import time
import os

# --- Configuration ---
FIREBASE_URL = "https://machine-guard-21f0a-default-rtdb.firebaseio.com/sensor_readings/esp32.json"
MODEL_PATH = "test_model.pkl"
SCALER_PATH = "test_scaler.pkl"
TRAINING_DATA_PATH = "training_data.csv"
TEST_DATA_PATH = "motor_test_data.csv"
POLL_INTERVAL = 2.0  # Seconds

feature_names = ["temperature", "humidity", "gas", "vibration", "current"]

# --- Load Artifacts ---
print("Loading model and scaler...")
try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print("Model and scaler loaded successfully.")
except FileNotFoundError:
    print(f"Error: Could not find {MODEL_PATH} or {SCALER_PATH}. Please ensure training artifacts exist.")
    exit(1)

# --- Load Data for Baseline ---
try:
    if os.path.exists(TRAINING_DATA_PATH):
        data = pd.read_csv(TRAINING_DATA_PATH)
        # Ensure 'current' column exists if 'power' was used or similar
        # Assuming training_data has correct columns
        data = data[feature_names]
    else:
        print(f"Warning: {TRAINING_DATA_PATH} not found. Generating dummy baseline.")
        data = pd.DataFrame({
            "temperature": np.random.normal(55, 2, 100),
            "humidity": np.random.normal(50, 5, 100),
            "gas": np.random.normal(120, 10, 100),
            "vibration": np.random.normal(0.35, 0.07, 100),
            "current": np.random.normal(4.5, 0.4, 100) 
        })
except Exception as e:
    print(f"Error loading training data: {e}")
    exit(1)

# --- User Provided Logic Blocks ---

# Store baseline statistics from normal training data
baseline_mean = data.mean()
baseline_std = data.std()
feature_names = data.columns.tolist()


def analyze_sensor_contribution(sample):
    """
    Calculates Z-score deviation of a sample from normal baseline.
    Returns sensors ranked by contribution to anomaly.
    """
    # Convert to Series if needed
    if isinstance(sample, (np.ndarray, list)):
        sample = pd.Series(sample, index=feature_names)

    # Compute Z-scores relative to baseline
    z_scores = (sample - baseline_mean) / baseline_std
    contributions = dict(zip(feature_names, np.abs(z_scores)))

    # Sort sensors by highest deviation
    sorted_contrib = sorted(contributions.items(), key=lambda item: item[1], reverse=True)
    return sorted_contrib


def classify_risk(health_score):
    """
    Classifies risk level based on health percentage.
    """
    if health_score > 80:
        return "NORMAL"
    elif 50 < health_score <= 80:
        return "WARNING"
    else:
        return "CRITICAL"

def generate_alert(risk, health, top_factors):
    """
    Generates an industrial-style alert message.
    """
    if risk == "NORMAL":
        return f"[OK] System Healthy (Score: {health:.1f}%)"
    
    # Construct alert message with all contributing factors
    alert = f"[{risk}] Action Required! Health: {health:.1f}% | "
    
    contributors = []
    for factor, deviation in top_factors:
        # Include factors with significant deviation (e.g., > 1.5 sigma)
        if deviation > 1.5:
            contributors.append(f"{factor.upper()} (Deviation: {deviation:.2f}σ)")
            
    # Fallback: if no factor > 1.5, show at least the top one
    if not contributors and top_factors:
        primary_cause, primary_dev = top_factors[0]
        contributors.append(f"{primary_cause.upper()} (Deviation: {primary_dev:.2f}x)")
        
    alert += " | ".join(contributors)
    
    return alert

# Helper function needed for user's code block but not provided in snippet
def calculate_health_score(anomaly_score):
    """
    Maps anomaly score (lower is worse) to a health percentage (0-100%).
    """
    # Clip score for mapping consistency
    # Notebook logic: map -0.5 (bad) to 0.2 (good) approximately
    score_clipped = np.clip(anomaly_score, -0.5, 0.2)
    norm_score = (score_clipped - (-0.5)) / (0.2 - (-0.5))
    health_percentage = norm_score * 100
    return np.int32(max(0, min(100, health_percentage))) # Return scalar or array depending on input

# --- Simulation Block (Requested by User) ---
# Check if test data exists to run the simulation loop
if os.path.exists(TEST_DATA_PATH):
    print("\n--- RUNNING SIMULATION SELF-TEST (User Request) ---")
    try:
        test_data = pd.read_csv(TEST_DATA_PATH)
        # Ensure columns match
        test_data = test_data[feature_names] 
        print(f"Loaded test data: {test_data.shape}")

        # Scale entire test set
        test_data_scaled = scaler.transform(test_data)

        # Calculate Health Scores via Model
        # Note: Model returns scores for array input
        raw_scores = model.decision_function(test_data_scaled)
        
        # Vectorized mapping for simulation
        # Logic: ((np.clip(score, -0.5, 0.2) + 0.5) / 0.7) * 100
        scores = ((np.clip(raw_scores, -0.5, 0.2) + 0.5) / 0.7) * 100
        
        # Simulation Loop
        history = []

        print("--- REAL-TIME MONITORING LOG (SIMULATION) ---")
        for i in range(len(test_data)):

            # Simulated periodic check
            if i % 5 == 0:
                current_health = scores[i]
                risk_level = classify_risk(current_health)

                if risk_level != "NORMAL":
                    top_factors = analyze_sensor_contribution(test_data.iloc[i])
                    alert = generate_alert(risk_level, current_health, top_factors)
                    print(f"Time {i}: {alert}")
                else:
                    print(f"Time {i}: [INFO] Running Optimal. Health: {current_health:.1f}%")

            history.append(scores[i])

        print("--- MONITORING END (SIMULATION) ---\n")
    except Exception as e:
        print(f"Simulation skipped due to error: {e}")
else:
    print(f"Test data ({TEST_DATA_PATH}) not found. Skipping simulation loop.")


# --- Real-Time Firebase Monitor ---

train_scaled = scaler.transform(data)
train_scores = model.decision_function(train_scaled)

max_nice = np.percentile(train_scores, 99)
min_anom = np.percentile(train_scores, 1)

def map_health(score):
    xp = [min_anom, 0.0, max_nice]
    fp = [0, 50, 100]
    return np.interp(score, xp, fp)


def fetch_data():
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

print("--- STARTING LIVE FIREBASE MONITORING ---")

try:
    while True:
        data_json = fetch_data()
        
        if data_json:
            timestamp = data_json.get("timestamp", "N/A")
            
            try:
                # Map Firebase 'power' -> 'current'
                single_row = pd.DataFrame([{
                    "temperature": float(data_json.get("temperature", 0)),
                    "humidity": float(data_json.get("humidity", 0)),
                    "gas": float(data_json.get("gas", 0)),
                    "vibration": float(data_json.get("vibration", 0)),
                    "current": float(data_json.get("power", 0)) 
                }])
                
                # Scale
                single_scaled = scaler.transform(single_row)
                
                # Score
                raw_score = model.decision_function(single_scaled)[0]
                
                # Health
                # Reusing the vectorized logic for scalar:
                health = map_health(raw_score)

                
                risk = classify_risk(health)
                
                if risk != "NORMAL":
                    top_factors = analyze_sensor_contribution(single_row.iloc[0])
                    msg = generate_alert(risk, health, top_factors)
                else:
                    msg = f"[OK] System Healthy (Score: {health:.1f}%) - Time: {timestamp}"
                
                print(msg)
                
            except Exception as e:
                print(f"Error processing packet: {e}")
        
        time.sleep(POLL_INTERVAL)

except KeyboardInterrupt:
    print("\nStopped.")

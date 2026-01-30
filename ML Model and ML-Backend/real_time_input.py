import joblib
import json
import pandas as pd
import numpy as np
import os
import sys

def analyze_sensor_contribution(sample_df, scaler, feature_names):
    """Diagnoses which sensor is causing the anomaly."""
    sample_scaled = scaler.transform(sample_df)[0]
    contributions = dict(zip(feature_names, np.abs(sample_scaled)))
    sorted_contrib = sorted(contributions.items(), key=lambda item: item[1], reverse=True)
    return sorted_contrib

def calculate_health_score(X_scaled, config):
    """Reconstructs the health scoring logic from config."""
    raw_scores = model.decision_function(X_scaled)
    xp = [config["min_bad_score"], config["decision_boundary"], config["max_nice_score"]]
    fp = [0, 50, 100]
    health = np.interp(raw_scores, xp, fp, left=0, right=100)
    return health[0] # Return scalar

def classify_risk(health_score):
    if health_score > 80: return "NORMAL"
    elif 50 < health_score <= 80: return "WARNING"
    else: return "CRITICAL"

# Load Artifacts Global
try:
    print("Loading System Artifacts...")
    model = joblib.load("motor_model.pkl")
    scaler = joblib.load("motor_scaler.pkl")
    with open("calibration_config.json", "r") as f:
        config = json.load(f)
    print("System Loaded Successfully.")
except FileNotFoundError:
    print("Error: Calibration artifacts not found. Run 'python calibrate.py' first.")
    sys.exit(1)

def get_manual_input():
    print(f"\n--- Enter Sensor Readings ---")
    print("For reference (Normal avgs): Temp~55, Hum~50, Gas~120, Curr~4.5, Vib~0.35")
    
    try:
        temp = float(input("Temperature (C): ") or 55.0)
        hum = float(input("Humidity (%): ") or 50.0)
        gas = float(input("Gas (ppm): ") or 120.0)
        curr = float(input("Current (A): ") or 4.5)
        vib = float(input("Vibration (mm/s): ") or 0.35)
        
        return {
            'temperature': temp,
            'humidity': hum,
            'gas': gas,
            'current': curr,
            'vibration': vib
        }
    except ValueError:
        print("Invalid input. Please enter numbers.")
        return None

def main():
    print("Real-Time Anomaly Detection Interface")
    print("Type Ctrl+C to exit.")
    
    while True:
        reading = get_manual_input()
        if not reading: continue
        
        # Create DataFrame
        feature_names = config["feature_names"]
        sample_df = pd.DataFrame([reading], columns=feature_names)
        
        # Scale
        sample_scaled = scaler.transform(sample_df)
        
        # Analyze
        health = calculate_health_score(sample_scaled, config)
        risk = classify_risk(health)
        
        print("\n--- Diagnosis ---")
        print(f"Health Score: {health:.1f}%")
        print(f"Status:       [{risk}]")
        
        if risk != "NORMAL":
            top_features = analyze_sensor_contribution(sample_df, scaler, feature_names)
            primary = top_features[0]
            print(f"Root Cause:   {primary[0].upper()} (Deviation: {primary[1]:.1f}x)")
        else:
            print("System looks good.")
        print("-" * 30)

if __name__ == "__main__":
    main()

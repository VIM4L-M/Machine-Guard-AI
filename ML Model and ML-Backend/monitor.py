import pandas as pd
import numpy as np
import joblib
import json
import os
import sys

def analyze_sensor_contribution(sample, scaler, feature_names):
    """
    Calculates Z-scores to find which sensor deviates most from the mean.
    """
    # Create DataFrame for single sample to use scaler
    sample_df = pd.DataFrame([sample], columns=feature_names)
    sample_scaled = scaler.transform(sample_df)[0]
    
    # Z-score represents deviation magnitude
    contributions = dict(zip(feature_names, np.abs(sample_scaled)))
    
    # Sort by deviation
    sorted_contrib = sorted(contributions.items(), key=lambda item: item[1], reverse=True)
    return sorted_contrib

def classify_risk(health_score):
    if health_score > 80:
        return "NORMAL"
    elif 50 < health_score <= 80:
        return "WARNING"
    else:
        return "CRITICAL"

def generate_alert(risk, health, top_factors):
    if risk == "NORMAL":
        return f"[OK] System Healthy (Score: {health:.1f}%)"
    
    # Create explanation for anomaly
    primary_cause = top_factors[0][0]
    primary_dev = top_factors[0][1]
    
    alert = f"[{risk}] Action Required! Health: {health:.1f}% | "
    alert += f"Primary Cause: {primary_cause.upper()} (Deviation: {primary_dev:.1f}x)"
    
    return alert

def monitor_system(test_data_path="motor_test_data.csv", artifacts_dir="."):
    print("Initializing Monitoring System...")
    
    # Load Artifacts
    try:
        model = joblib.load(os.path.join(artifacts_dir, "motor_model.pkl"))
        scaler = joblib.load(os.path.join(artifacts_dir, "motor_scaler.pkl"))
        with open(os.path.join(artifacts_dir, "calibration_config.json"), "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: Calibration artifacts not found. Please run calibrate.py first.")
        return

    # Reconstruct Health Scorer
    max_nice = config["max_nice_score"]
    min_bad = config["min_bad_score"]
    decision_boundary = config["decision_boundary"]
    feature_names = config["feature_names"]
    
    xp = [min_bad, decision_boundary, max_nice]
    fp = [0, 50, 100]
    
    print(f"Loaded System Config: 100% Health at {max_nice:.4f}")

    # Load Simulation Data
    try:
        data = pd.read_csv(test_data_path)
    except FileNotFoundError:
        print(f"Error: Test data {test_data_path} not found.")
        return
        
    print(f"Starting Real-Time Monitoring Simulation on {len(data)} samples...")
    print("-" * 60)
    
    # Filter data to match training features (ignoring labels like 'is_anomaly')
    X_input = data[feature_names]
    
    # Pre-scale data for scoring (batch processing for efficiency in simulation)
    # In real deployment, we'd scale one by one
    X_scaled = scaler.transform(X_input)
    
    # Calculate Raw Scores
    raw_scores = model.decision_function(X_scaled)
    
    # Calculate Health Scores via Interpolation
    health_scores = np.interp(raw_scores, xp, fp, left=0, right=100)
    
    # Simulation Loop
    for i in range(len(data)):
        # Simulate sporadic checks (every 25th sample for readability)
        if i % 25 == 0:
            current_health = health_scores[i]
            risk_level = classify_risk(current_health)
            
            if risk_level != "NORMAL":
                top_factors = analyze_sensor_contribution(data.iloc[i], scaler, feature_names)
                alert = generate_alert(risk_level, current_health, top_factors)
                print(f"Time {i}: {alert}")
            else:
                print(f"Time {i}: [INFO] Running Optimal. Health: {current_health:.1f}%")

    print("-" * 60)
    print("Monitoring Session Ended.")

if __name__ == "__main__":
    monitor_system()

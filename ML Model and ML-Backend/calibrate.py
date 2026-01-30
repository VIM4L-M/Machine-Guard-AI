import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import json
import os

def calibrate_system(training_data_path="motor_normal_data.csv", artifacts_dir="."):
    print(f"Loading training data from {training_data_path}...")
    try:
        data = pd.read_csv(training_data_path)
    except FileNotFoundError:
        print(f"Error: File {training_data_path} not found.")
        return

    # Select features (excluding timestamp if present, but our csv is just sensor data)
    # Assuming all columns in the CSV are sensor readings
    X = data.copy()
    
    print("Training Scaler...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print("Training Isolation Forest Model (Self-Learning Phase)...")
    # Using contamination=0.01 as a starting point for "clean" normal data
    # or 0.05 if we expect some noise. Sticking to 0.05 as per notebook exploration.
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(X_scaled)
    
    print("Calibrating Health Score Thresholds...")
    train_scores = model.decision_function(X_scaled)
    
    # 1. Best Normal Score (100% Health Reference)
    # We use 99th percentile to be robust against outliers in the "good" data
    max_nice = float(np.percentile(train_scores, 99))
    
    # 2. Anomaly Threshold (0% Health Reference)
    # The model's decision boundary is 0.0. 
    # We define a "Worst Case" anomaly floor. 
    # In IF, scores < 0 are anomalies. -0.25 is a reasonable "very bad" floor based on previous analysis.
    min_bad = -0.25
    
    calibration_config = {
        "max_nice_score": max_nice,
        "decision_boundary": 0.0,
        "min_bad_score": min_bad,
        "feature_names": list(X.columns)
    }
    
    print(f"[Calibration Result] 100% Health Score: {max_nice:.4f}")
    print(f"[Calibration Result] 50% Health Score: 0.0 (Decision Boundary)")
    print(f"[Calibration Result] 0% Health Score: {min_bad}")
    
    # Save Artifacts
    print("Saving System Artifacts...")
    joblib.dump(model, os.path.join(artifacts_dir, "motor_model.pkl"))
    joblib.dump(scaler, os.path.join(artifacts_dir, "motor_scaler.pkl"))
    
    config_path = os.path.join(artifacts_dir, "calibration_config.json")
    with open(config_path, "w") as f:
        json.dump(calibration_config, f, indent=4)
        
    print(f"System Calibrated! Artifacts saved to {artifacts_dir}")

if __name__ == "__main__":
    calibrate_system()

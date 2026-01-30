import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Configuration
MODEL_PATH = "test_model.pkl"
SCALER_PATH = "test_scaler.pkl"
DATA_PATH = "training_data.csv"

def load_and_preprocess_data():
    print("Libraries loaded successfully.")
    
    # Load Data
    try:
        data = pd.read_csv(DATA_PATH)
        print(f"Dataset loaded: {data.shape}")
    except FileNotFoundError:
        print("Error: Dataset not found. Please run dataset_gen.py first.")
        # Creating dummy data for notebook flow if file missing (Fallback)
        data = pd.DataFrame({
            "temperature": np.random.normal(55, 2, 500),
            "humidity": np.random.normal(50, 5, 500),
            "gas": np.random.normal(120, 10, 500),
            "current": np.random.normal(4.5, 0.4, 500),
            "vibration": np.random.normal(0.35, 0.07, 500)
        })

    # Standardization
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(data)

    # Save Scaler for real-time usage
    joblib.dump(scaler, SCALER_PATH)
    print("Scaler saved.")
    print("Feature statistics before scaling:")
    print(data.describe().loc[['mean', 'std']])
    print("Scaled feature shape:", X_scaled.shape)
    
    return data, X_scaled, scaler

def train_model(X_scaled):
    # We use Isolation Forest with a contamination factor of 0.05
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05, # Conservative estimate for calibration
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_scaled)

    # Save Model
    joblib.dump(model, MODEL_PATH)
    print("Model trained and saved successfully.")
    
    return model

def get_calibrated_scorer(model, X_train_scaled):
    """
    Creates a health scorer calibrated to the training data distribution.

    Mapping:
      Worst observed anomaly (1st percentile) -> 0% Health
      Isolation Forest decision boundary (0.0) -> 50% Health
      Best normal behavior (99th percentile) -> 100% Health
    """
    # Get decision scores from training data
    train_scores = model.decision_function(X_train_scaled)

    # Robust bounds
    max_nice = np.percentile(train_scores, 99)   # Best normal region
    min_anom = np.percentile(train_scores, 1)    # Worst anomaly region

    # Interpolation points
    xp = [min_anom, 0.0, max_nice]   # Score scale
    fp = [0, 50, 100]                # Health scale

    print(f"[System Calibration]")
    print(f"  0% Health at score ≈ {min_anom:.4f}")
    print(f"  50% Health at decision boundary (0.0)")
    print(f"  100% Health at score ≈ {max_nice:.4f}")

    def calculate_health(X_input):
        raw_scores = model.decision_function(X_input)
        # Linear interpolation with clamping
        health = np.interp(raw_scores, xp, fp, left=0, right=100)
        return health

    return calculate_health

def plot_health_distribution(model, X_train_scaled, calculate_health_score, show_plot=False):
    if not show_plot:
        return
        
    # Compute health for training data
    train_health = calculate_health_score(X_train_scaled)

    # Visualization
    plt.figure(figsize=(10, 4))
    plt.hist(train_health, bins=30, color='green', alpha=0.7)
    plt.title("Calibrated Health Score Distribution (Training Data)")
    plt.xlabel("Health %")
    plt.ylabel("Count")
    plt.axvline(x=50, color='red', linestyle='--', label="Anomaly Boundary (50%)")
    plt.legend()
    plt.show()

def generate_stress_data(base_data, fault_type="none", intensity=1.5):
    df = base_data.copy()

    if fault_type == "overheat":
        df['temperature'] += 15 * (intensity - 1)

    elif fault_type == "vibration_imbalance":
        df['vibration'] += 0.3 * (intensity - 1)

    elif fault_type == "voltage_sag":
        df['current'] += 1.5 * (intensity - 1)

    elif fault_type == "combined":
        df['temperature'] += 10
        df['vibration'] += 0.4

    return df

def generate_test_set(data):
    # Create test set: 100 Normal, 50 Overheat, 50 High Vibration
    test_normal = data.sample(100, random_state=1).reset_index(drop=True)
    test_overheat = generate_stress_data(data.sample(50, random_state=2), "overheat", 1.8)
    test_vibration = generate_stress_data(data.sample(50, random_state=3), "vibration_imbalance", 2.5)

    # Combine
    test_data = pd.concat([test_normal, test_overheat, test_vibration]).reset_index(drop=True)
    test_labels = [0]*100 + [1]*50 + [1]*50 # 0=Normal, 1=Anomaly

    print("Test Data Generated:", test_data.shape)
    return test_data

# Store baseline statistics from normal training data
def get_analysis_functions(data):
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

    return analyze_sensor_contribution

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
        contributors.append(f"{primary_cause.upper()} (Deviation: {primary_dev:.2f}σ)")
        
    alert += " | ".join(contributors)
    
    return alert

def run_simulation(test_data, scaler, calculate_health_score, analyze_sensor_contribution):
    # Scale entire test set
    test_data_scaled = scaler.transform(test_data)

    # Calculate Health Scores
    scores = calculate_health_score(test_data_scaled)

    # Simulation Loop
    history = []

    print("--- REAL-TIME MONITORING LOG ---")
    for i in range(len(test_data)):

        # Simulated periodic check
        if i % 25 == 0:
            current_health = scores[i]
            risk_level = classify_risk(current_health)

            if risk_level != "NORMAL":
                top_factors = analyze_sensor_contribution(test_data.iloc[i])
                alert = generate_alert(risk_level, current_health, top_factors)
                print(f"Time {i}: {alert}")
            else:
                print(f"Time {i}: [INFO] Running Optimal. Health: {current_health:.1f}%")

        history.append(scores[i])

    print("--- MONITORING END ---")
    return history

def plot_trends(history, show_plot=False):
    if not show_plot:
        return
        
    plt.figure(figsize=(12, 5))
    plt.plot(history, label="Health Score", color='blue')
    plt.axhline(y=50, color='red', linestyle='--', label="Critical Threshold")
    plt.axhline(y=80, color='orange', linestyle='--', label="Warning Threshold")
    plt.title("Machine Health Trend Over Time (Simulated)")
    plt.ylabel("Health Score (%)")
    plt.xlabel("Time Steps")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

def main():
    # 1. Load & Preprocess
    data, X_scaled, scaler = load_and_preprocess_data()
    
    # 2. Train Model
    model = train_model(X_scaled)
    
    # 3. Calibration
    calculate_health_score = get_calibrated_scorer(model, X_scaled)
    
    # (Optional) Plot health distribution
    # plot_health_distribution(model, X_scaled, calculate_health_score, show_plot=False)
    
    # 4. Stress Testing
    test_data = generate_test_set(data)
    
    # 5. Analysis Setup
    analyze_sensor_contribution = get_analysis_functions(data)
    
    # 6. Real-Time Simulation
    history = run_simulation(test_data, scaler, calculate_health_score, analyze_sensor_contribution)
    
    # (Optional) Plot trends
    # plot_trends(history, show_plot=False)

if __name__ == "__main__":
    main()

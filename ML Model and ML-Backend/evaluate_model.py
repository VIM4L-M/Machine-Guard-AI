import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import classification_report, confusion_matrix

# Load resources
try:
    model = joblib.load("motor_model.pkl")
    scaler = joblib.load("scaler.pkl")
    data = pd.read_csv("motor_test_data.csv")
except FileNotFoundError as e:
    print(f"Error loading files: {e}")
    print("Please make sure training has been run and test data generated.")
    exit(1)

# Prepare Features
X = data.drop("is_anomaly", axis=1)
y_true = data["is_anomaly"] # 0 for normal, 1 for anomaly

# Scale Data
X_scaled = scaler.transform(X)

# Predict
# Isolation Forest returns 1 for inliers (normal), -1 for outliers (anomaly)
preds_raw = model.predict(X_scaled)

# Convert predictions to match ground truth: 1 -> 0 (Normal), -1 -> 1 (Anomaly)
y_pred = np.where(preds_raw == 1, 0, 1)

# Evaluation
print("--- Evaluation Results ---")
print(confusion_matrix(y_true, y_pred))
print("\n")
print(classification_report(y_true, y_pred, target_names=["Normal", "Anomaly"]))

# Calculate Health Scores for Anomalies
scores = model.decision_function(X_scaled)
# Approx heuristic: score < 0 is anomaly. The more negative, the more anomalous.
# To convert to 0-100 health score (very rough approximation):
# We take max score as baseline ~100%, and degrade as it drops.
# Since scores are just distances, we normalize a bit based on training distribution assumption.
# For simplicity, let's look at raw scores of anomalies vs normal.

data["score"] = scores
print("\n--- Average Decision Function Score ---")
print(data.groupby("is_anomaly")["score"].mean())

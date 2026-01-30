
import os
import time
import json
import requests
import joblib
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt
from collections import deque
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# --- Configuration ---
FIREBASE_URL_ROOT = "https://machine-guard-21f0a-default-rtdb.firebaseio.com/sensor_readings.json"
MODELS_DIR = "models"
POLL_INTERVAL = 2.0  # Seconds
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
CALIBRATION_SAMPLES = 100
MAX_CALIBRATION_TIME = 300 # Seconds (5 minutes)

# Ensure models directory exists
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

# --- Shared Logic ---
FEATURES = ["temperature", "humidity", "gas", "vibration", "current"]

# --- Device Manager Class ---
class DeviceManager:
    def __init__(self, device_id, mqtt_client):
        self.device_id = device_id
        self.mqtt_client = mqtt_client
        self.state_file = os.path.join(MODELS_DIR, f"{device_id}_state.json")
        self.training_file = os.path.join(MODELS_DIR, f"{device_id}_training.csv")
        self.model_file = os.path.join(MODELS_DIR, f"{device_id}_model.pkl")
        self.scaler_file = os.path.join(MODELS_DIR, f"{device_id}_scaler.pkl")
        
        # Runtime State
        self.state = self.load_state()
        self.calibration_start_time = None
        self.model = None
        self.scaler = None
        self.baseline_stats = {}
        self.score_mapping = {}
        self.last_processed_ts = None
        
        # Monitoring Buffers
        self.sensor_buffer = deque(maxlen=1) # No Smoothing (Real-time)
        self.health_history = deque(maxlen=3) # Alert Persistence
        self.last_risk = "NORMAL"

        if self.state == "MONITORING":
            self.load_artifacts()

    def load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    s = data.get("state", "NEW")
                    print(f"[{self.device_id}] Loaded State: {s}")
                    return s
            except:
                pass

        # Check if model artifacts already exist (Skip Calibration)
        if os.path.exists(self.model_file) and os.path.exists(self.scaler_file):
            print(f"[{self.device_id}] Found existing artifacts. Skipping calibration -> MONITORING.")
            return "MONITORING"
            
        print(f"[{self.device_id}] Initial State: NEW")
        return "NEW"

    def save_state(self, new_state):
        self.state = new_state
        with open(self.state_file, 'w') as f:
            json.dump({"state": new_state}, f)
        print(f"[{self.device_id}] State changed to: {new_state}")

    def process_reading(self, reading):
        # Map fields (power -> current)
        mapped_reading = {
            "temperature": reading.get("temperature", 0),
            "humidity": reading.get("humidity", 0),
            "gas": reading.get("gas", 0),
            "vibration": reading.get("vibration", 0),
            "current": reading.get("power", 0)
        }
        
        if self.state == "NEW":
            self.start_calibration()
            self.append_training_data(mapped_reading)
            
        elif self.state == "CALIBRATING":
            self.handle_calibration(mapped_reading)
            
        elif self.state == "MONITORING":
            self.handle_monitoring(mapped_reading)

    def start_calibration(self):
        print(f"[{self.device_id}] Starting Calibration...")
        # Reset training file
        if os.path.exists(self.training_file):
            os.remove(self.training_file)
        
        # Create file with header
        pd.DataFrame(columns=FEATURES).to_csv(self.training_file, index=False)
        
        self.calibration_start_time = time.time()
        self.save_state("CALIBRATING")

    def append_training_data(self, row_dict):
        df = pd.DataFrame([row_dict])
        df.to_csv(self.training_file, mode='a', header=False, index=False)

    def handle_calibration(self, reading):
        self.append_training_data(reading)
        
        # Check counts
        try:
            # Efficient line counting would be better for prod, but pd is fine for N=150
            df = pd.read_csv(self.training_file)
            count = len(df)
            elapsed = time.time() - (self.calibration_start_time or time.time())
            
            if count >= CALIBRATION_SAMPLES or elapsed > MAX_CALIBRATION_TIME:
                print(f"[{self.device_id}] Calibration complete (N={count}, Time={elapsed:.1f}s). Training...")
                self.train_model(df)
                self.save_state("MONITORING")
                self.load_artifacts() # Load what we just trained
            elif count % 10 == 0:
                 print(f"[{self.device_id}] Calibrating... ({count}/{CALIBRATION_SAMPLES})")
                 
        except Exception as e:
            print(f"[{self.device_id}] Calibration error: {e}")

    def train_model(self, df):
        try:
            # 1. Preprocessing (Match Notebook: Just Scale)
            # Notebook does not noise inject.
            
            # 2. Scaling
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(df[FEATURES])
            joblib.dump(scaler, self.scaler_file)

            # 3. Training
            # Match params: n_estimators=200, contamination=0.05, random_state=42
            model = IsolationForest(
                n_estimators=200, 
                contamination=0.05, 
                random_state=42, 
                n_jobs=-1
            )
            model.fit(X_scaled)
            joblib.dump(model, self.model_file)

            # 4. Calibration Stats (Health Score Map)
            scores = model.decision_function(X_scaled)
            
            # Match percentiles: 1st and 99th
            min_anom = float(np.percentile(scores, 1))
            max_nice = float(np.percentile(scores, 99))
            
            stats = {
                "min_anom": min_anom,
                "max_nice": max_nice,
                "baseline_mean": df[FEATURES].mean().to_dict(),
                "baseline_std": df[FEATURES].std().to_dict()
            }
            
            with open(os.path.join(MODELS_DIR, f"{self.device_id}_calibration.json"), 'w') as f:
                json.dump(stats, f)
                
            print(f"[{self.device_id}] Training successful.")
            
        except Exception as e:
            print(f"[{self.device_id}] Training Failed: {e}")
            # Reset to NEW
            self.save_state("NEW")

    def load_artifacts(self):
        try:
            self.model = joblib.load(self.model_file)
            self.scaler = joblib.load(self.scaler_file)
            with open(os.path.join(MODELS_DIR, f"{self.device_id}_calibration.json"), 'r') as f:
                stats = json.load(f)
                self.score_mapping = stats
                self.baseline_stats = stats
            print(f"[{self.device_id}] Artifacts loaded.")
        except Exception as e:
            print(f"[{self.device_id}] Artifact load error: {e}. Re-calibrating.")
            self.save_state("NEW")

    def map_health(self, raw_score):
        xp = [self.score_mapping["min_anom"], 0.0, self.score_mapping["max_nice"]]
        fp = [0, 50, 100]
        return np.interp(raw_score, xp, fp)

    def analyze_sensor_contribution(self, sample):
        """
        Calculates Z-score deviation of a sample from normal baseline.
        Returns sensors ranked by contribution to anomaly.
        """
        means = pd.Series(self.baseline_stats["baseline_mean"])
        stds = pd.Series(self.baseline_stats["baseline_std"])
        stds = stds.replace(0, 1e-6) # Avoid zero division

        # Compute Z-scores relative to baseline
        z_scores = (sample - means) / stds
        contributions = dict(zip(FEATURES, np.abs(z_scores)))

        # Sort sensors by highest deviation
        sorted_contrib = sorted(contributions.items(), key=lambda item: item[1], reverse=True)
        return sorted_contrib

    def generate_alert(self, risk, health, top_factors):
        """
        Generates an industrial-style alert message.
        """
        if risk == "NORMAL":
            return f"[OK] System Healthy (Score: {health:.1f}%)"
        
        # Construct alert message with all contributing factors
        alert = f"[{risk}] Action Required! Health: {health:.1f}% | "
        
        contributors = []
        for factor, deviation in top_factors:
            # Include only significant deviations (> 2.0x)
            if deviation > 2.0:
                contributors.append(f"{factor.upper()} (Deviation: {deviation:.2f}x)")
                
        # Fallback: if no factor > 1.5, show at least the top one
        if not contributors and top_factors:
            primary_cause, primary_dev = top_factors[0]
            contributors.append(f"{primary_cause.upper()} (Deviation: {primary_dev:.2f}x)")
            
        alert += " | ".join(contributors)
        return alert

    def handle_monitoring(self, reading):
        if not self.model: 
            return

        try:
            # 1. Smoothing
            self.sensor_buffer.append(reading)
            df_buffer = pd.DataFrame(list(self.sensor_buffer))
            smoothed = df_buffer.mean().to_frame().T
            current_vals = smoothed.iloc[0]
            
            # 2. Scoring
            scaled = self.scaler.transform(smoothed[FEATURES])
            raw_score = self.model.decision_function(scaled)[0]
            health = self.map_health(raw_score)
            
            # 3. Risk Logic
            risk = "NORMAL"
            if health < 30: risk = "CRITICAL"
            elif health < 60: risk = "WARNING"
            
            # 4. Persistence Buffer (Only for MQTT Alert triggering?)
            # User wants visual output like firebase_monitor.py which prints EVERYTHING.
            # But we should keep the suppression logic for MQTT to avoid spam.
            self.health_history.append(health)
            
            # 5. Generate Console Message (Always)
            if risk != "NORMAL":
                top_factors = self.analyze_sensor_contribution(current_vals)
                msg = self.generate_alert(risk, health, top_factors)
            else:
                msg = f"[OK] System Healthy (Score: {health:.1f}%)"

            # Print with ID prefix
            print(f"[{self.device_id}] {msg}")

            # 6. MQTT Logic (Keep persistent check to avoid spam)
            should_publish_mqtt = False
            is_persistent_crit = (len(self.health_history) == 3 and all(h < 50 for h in self.health_history))
            
            if risk == "CRITICAL" and is_persistent_crit:
                should_publish_mqtt = True
            elif risk == "WARNING" and self.last_risk != "WARNING": 
                should_publish_mqtt = True
            elif risk == "NORMAL" and self.last_risk != "NORMAL":
                should_publish_mqtt = True
                
            self.last_risk = risk

            # Publish if needed (or always? The requirement was to send anomalies)
            # Let's keep publishing always for graph, but alerts are implicit in the data
            
            primary_issue = "NONE"
            if risk != "NORMAL":
                top_factors = self.analyze_sensor_contribution(current_vals)
                # Format: "TEMP (Deviation: 5.2σ) | VIB (Deviation: 3.1σ)"
                contributors = []
                for factor, deviation in top_factors:
                    if deviation > 2.0:
                        contributors.append(f"{factor.upper()} (Deviation: {deviation:.2f}x)")
                
                if not contributors and top_factors:
                    f, d = top_factors[0]
                    contributors.append(f"{f.upper()} (Deviation: {d:.2f}x)")
                    
                primary_issue = " | ".join(contributors)

            # Prepare full sensor report (always included)
            # analyze_sensor_contribution returns all features sorted by deviation
            factor_list = self.analyze_sensor_contribution(current_vals)
            sensor_report = {}
            for factor, deviation in factor_list:
                sensor_report[factor] = {
                    "value": round(current_vals[factor], 2),
                    "deviation": round(deviation, 2)
                }

            payload = {
                "device_id": self.device_id,
                "health": round(health, 1),
                "risk": risk,
                "primary_issue": primary_issue,
                "sensors": sensor_report,
                "timestamp": time.time()
            }
            
            topic = f"machine_guard/{self.device_id}/status"
            self.mqtt_client.publish(topic, json.dumps(payload))
            
        except Exception as e:
            print(f"[{self.device_id}] Monitoring error: {e}")


# --- Master System ---
class MachineGuardSystem:
    def __init__(self):
        self.devices = {} # {device_id: DeviceManager}
        self.mqtt_client = mqtt.Client()
        self.connect_mqtt()

    def connect_mqtt(self):
        try:
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            print(f"Connected to MQTT Broker: {MQTT_BROKER}")
        except Exception as e:
            print(f"MQTT Connection Failed: {e}")

    def poll_firebase(self):
        try:
            response = requests.get(FIREBASE_URL_ROOT)
            if response.status_code == 200 and response.json():
                return response.json() # Dictionary of {device_id: {data...}} or {device_id: data} depending on structure
            return {}
        except Exception as e:
            print(f"Firebase Poll Error: {e}")
            return {}

    def run(self):
        print("Machine Guard Core Active. Polling Firebase...")
        try:
            while True:
                data_tree = self.poll_firebase()
                
                # Iterate through devices
                # Structure assumption: sensor_readings -> { "esp32": {fields...}, "device2": {fields...} }
                for device_id, reading in data_tree.items():
                    if not isinstance(reading, dict): continue
                    
                    # Init device manager if new
                    if device_id not in self.devices:
                        print(f"New Device Detected: {device_id}")
                        self.devices[device_id] = DeviceManager(device_id, self.mqtt_client)
                    
                    # Process Lifecycle
                    from datetime import datetime
                    
                    # Logic: 
                    # 1. Ignore if timestamp matches last processed (Duplicate)
                    # 2. Ignore if timestamp is significantly older than the freshest device (Stale/Inactive)
                    
                    ts_str = reading.get("timestamp")
                    if not ts_str:
                        continue
                        
                    # Skip if we already processed this EXACT timestamp
                    last_processed = self.devices[device_id].last_processed_ts
                    if last_processed == ts_str:
                        continue 
                        
                    # Update the last processed
                    self.devices[device_id].last_processed_ts = ts_str

                    # Check for Staleness relative to NOW (Active Selection)
                    # ... [comments] ...
                    
                    if device_id == "esp32_Machine_1":
                         # print(f"[DEBUG] {device_id} TS: {ts_str} | Last: {last_processed}")
                         pass

                    self.devices[device_id].process_reading(reading)
                
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\nShutting down.")
            self.mqtt_client.loop_stop()

if __name__ == "__main__":
    system = MachineGuardSystem()
    system.run()

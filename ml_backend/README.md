# ML Backend - Real-Time Anomaly Detection

This is the Machine Learning backend for Machine-Guard that subscribes directly to the MQTT broker and performs real-time anomaly detection and failure prediction.

## Architecture

```
ESP32 Device
    ↓
    └─→ MQTT Broker (broker.hivemq.com)
           ↓
           └─→ ML Backend (This Service)
                   ↓
                   ├─→ Anomaly Detection
                   ├─→ Failure Prediction
                   ├─→ Health Scoring
                   └─→ Alert Generation
```

## Features

### 1. **Real-Time Data Processing**
   - Subscribes directly to MQTT broker
   - No database dependency
   - Low-latency processing
   - 2-second data refresh rate from ESP32

### 2. **Anomaly Detection**
   - Range-based detection (sensor limits)
   - Statistical deviation detection (Z-score)
   - Maintains historical data for comparison

### 3. **Failure Prediction**
   - Bearing failure detection (high vibration + temperature)
   - Combustible gas hazard detection
   - Sensor malfunction detection
   - Equipment breakdown prediction

### 4. **Health Scoring**
   - 0-100 health score
   - Based on anomalies and predictions
   - Real-time recommendation generation

### 5. **Alerting**
   - Critical alerts for failures
   - Warning alerts for anomalies
   - Extensible for email/SMS/Slack integration

## Setup

### 1. Install Dependencies

```bash
cd /home/ravi/Machine-Guard-AI/ml_backend
pip install -r requirements.txt
```

### 2. Configure MQTT Connection

Edit `.env` file with your MQTT settings:

```bash
# For local Mosquitto broker
MQTT_BROKER=127.0.0.1
MQTT_PORT=1883

# For HiveMQ public broker
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883

# Topic to subscribe to
MQTT_TOPIC=iot/esp32/test
```

### 3. Run the ML Backend

```bash
cd /home/ravi/Machine-Guard-AI/ml_backend
python app.py
```

## Output Example

```
======================================================================
✓ HEALTH REPORT - 2026-01-29T21:45:30.123456
======================================================================
Health Score: 85/100 (GOOD)
Recommendation: ✓ NORMAL: Equipment operating normally

Sensor Data:
  temperature     = 26.5
  humidity        = 45.2
  gas             = 850
  vibration       = 25
  power           = 2.8
```

## Data Flow

1. **ESP32 publishes** sensor data to `iot/esp32/test` topic
   ```json
   {
     "temperature": 26.5,
     "humidity": 45.2,
     "gas": 850,
     "vibration": 25,
     "current": 0.28
   }
   ```

2. **ML Backend receives** via MQTT subscription (real-time)

3. **Anomaly Detector analyzes** the data:
   - Checks against normal ranges
   - Compares with historical data
   - Calculates Z-scores

4. **Health Report generated** with:
   - Health score (0-100)
   - Anomalies detected
   - Failure predictions
   - Recommendations

5. **Results logged** for analysis and displayed in console

## Anomaly Detection Logic

### Rule 1: Range-Based Detection
```
Temperature: 15°C - 40°C (normal range)
Humidity: 20% - 80% (normal range)
Gas: 300 - 1500 ppm (normal range)
```

### Rule 2: Statistical Detection
```
Z-score > 2 → Deviation from historical mean
(2 standard deviations from mean)
```

## Failure Prediction Logic

### Bearing Failure
```
IF (vibration > 60 AND temperature > 35) THEN
   Risk: HIGH
   Action: Inspect bearings immediately
```

### Combustible Gas Hazard
```
IF (gas > 1200 ppm) THEN
   Risk: CRITICAL
   Action: Activate ventilation system
```

### Sensor Malfunction
```
IF (power < 0.1 W) THEN
   Risk: MEDIUM
   Action: Check sensor connections
```

## Health Score Calculation

```
Base Score: 100

Anomaly Penalty: -20 per anomaly
Failure Prediction Penalties:
  - Critical: -30
  - High: -15
  - Medium: -5

Final Score: 0-100
  - 80-100: GOOD (✓)
  - 60-79: FAIR (⚠️)
  - 40-59: POOR (⚠️)
  - 0-39: CRITICAL (⛔)
```

## Integration with Main Backend

The ML backend works **independently** but can optionally sync with the Flask backend:

### Option A: Independent (Current)
- ML Backend: Real-time predictions via MQTT
- Flask Backend: Data storage in Firebase
- No direct communication needed

### Option B: Integration
- ML Backend: Sends predictions to Flask API
- Flask Backend: Stores ML results in Firebase
- Combined system for storage + predictions

## Running Both Backends

### Terminal 1: Main Flask Backend
```bash
cd /home/ravi/Machine-Guard-AI/backend
source ../venv/bin/activate
python app.py
```

### Terminal 2: ML Backend
```bash
cd /home/ravi/Machine-Guard-AI/ml_backend
source ../venv/bin/activate
python app.py
```

## Key Advantages

✅ **Real-Time**: Direct MQTT connection, 2-second latency
✅ **Independent**: Works without Firebase/database
✅ **Lightweight**: No heavy storage operations
✅ **Scalable**: Can handle multiple MQTT topics
✅ **Extensible**: Easy to add new sensors/rules
✅ **Offline**: Processes data offline (no API calls needed)

## Extending the System

### Add Custom Detection Rules

Edit `anomaly_detector.py`:

```python
def detect_anomalies(self, sensor_data):
    # Add your custom logic here
    if sensor_data["temperature"] > 45:
        anomalies.append({
            "sensor": "temperature",
            "reason": "Custom high-temp alert",
            "severity": "critical"
        })
```

### Add Alert Integrations

Edit `app.py` in `_check_alerts()`:

```python
def _check_alerts(self, report):
    if report["health_score"] < 40:
        # Send email
        send_email("alert@company.com", "Low health score!")
        
        # Send to Slack
        send_slack_message("#alerts", report)
        
        # Send SMS
        send_sms("+91XXXXXXXXXX", "Equipment failure predicted!")
```

## Troubleshooting

### No Data Received
```bash
# Check MQTT broker connectivity
mosquitto_sub -h broker.hivemq.com -t "iot/esp32/test" -v

# Check .env configuration
cat .env
```

### High False Positives
- Adjust sensor ranges in `anomaly_detector.py`
- Increase history buffer size
- Tune Z-score threshold (currently 2.0)

### Performance Issues
- Reduce `max_history` size in `AnomalyDetector`
- Reduce `max_log_size` in `MLBackend`
- Filter unnecessary topics in MQTT subscription

## License

Machine-Guard ML Backend
Copyright © 2026

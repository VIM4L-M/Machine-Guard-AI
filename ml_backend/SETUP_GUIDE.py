#!/usr/bin/env python3
"""
ML Backend Setup & Usage Guide
Real-time anomaly detection from MQTT broker
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                 Machine-Guard ML Backend - SETUP GUIDE                    ║
╚════════════════════════════════════════════════════════════════════════════╝

## OPTION 1: ML Backend Subscribes to MQTT Directly ✅ RECOMMENDED

This is what we just built! Your ML backend now:

1. Connects to MQTT broker (broker.hivemq.com:1883)
2. Subscribes to 'iot/esp32/test' topic
3. Receives sensor JSON in real-time from ESP32
4. Performs anomaly detection & failure prediction
5. Generates health scores and alerts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## HOW IT WORKS - Data Flow

                    ESP32 Device
                        ↓
              publishes JSON every 2 seconds
                        ↓
         MQTT Broker (broker.hivemq.com:1883)
                        ↓
         ML Backend subscribes to 'iot/esp32/test'
                        ↓
              MLMQTTClient.on_message()
                        ↓
              AnomalyDetector.process()
                        ↓
         ┌─────────────────────────────┐
         │ Generate Health Report:     │
         │ - Health Score (0-100)      │
         │ - Anomalies Detected        │
         │ - Failure Predictions       │
         │ - Recommendations           │
         └─────────────────────────────┘
                        ↓
                  Display Results
                 + Alert if Critical

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## FILES CREATED

📁 /home/ravi/Machine-Guard-AI/ml_backend/
├── app.py                    ← Main application
├── mqtt_client.py            ← MQTT subscriber
├── anomaly_detector.py       ← ML detection logic
├── requirements.txt          ← Dependencies
├── .env                      ← Configuration
├── start.sh                  ← Quick start script
├── README.md                 ← Full documentation
└── __init__.py               ← Python package

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## INSTALLATION (One-time setup)

1. Navigate to ML backend directory:
   $ cd /home/ravi/Machine-Guard-AI/ml_backend

2. Activate virtual environment:
   $ source ../venv/bin/activate

3. Install dependencies:
   $ pip install -r requirements.txt

4. Configure MQTT settings (optional):
   $ cat .env
   # Shows current configuration
   # Default: broker.hivemq.com, port 1883, topic iot/esp32/test

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## RUNNING THE ML BACKEND

Method 1: Using the start script (easiest)
────────────────────────────────────────
$ cd /home/ravi/Machine-Guard-AI/ml_backend
$ ./start.sh

Method 2: Manual execution
──────────────────────────
$ cd /home/ravi/Machine-Guard-AI/ml_backend
$ source ../venv/bin/activate
$ python app.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## EXPECTED OUTPUT

When running, you should see:

    ======================================================================
    🤖 Machine-Guard ML Backend Starting...
    ======================================================================

    ✓ Connected to MQTT broker: broker.hivemq.com:1883
    ✓ Subscribed to topic: iot/esp32/test
    ✓ ML Backend is running. Press Ctrl+C to stop.

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## WHAT THE ML BACKEND DOES

1. REAL-TIME DATA RECEPTION
   ✓ Receives JSON from ESP32 via MQTT
   ✓ No database dependency
   ✓ ~2 second latency from sensor reading

2. ANOMALY DETECTION
   ✓ Range-based detection
     - Temperature: 15°C - 40°C
     - Humidity: 20% - 80%
     - Gas: 300 - 1500 ppm
     - Vibration: 0 - 100
     - Power: 0 - 10 W

   ✓ Statistical detection (Z-score)
     - Compares current value to historical mean
     - Flags if deviation > 2 standard deviations

3. FAILURE PREDICTION
   ✓ Bearing Failure: High vibration + high temperature
   ✓ Gas Hazard: Gas concentration > 1200 ppm
   ✓ Sensor Malfunction: Power < 0.1 W

4. HEALTH SCORING
   ✓ 0-100 score based on anomalies & predictions
   ✓ Automatic recommendations
   ✓ Severity levels (normal, medium, high, critical)

5. ALERT GENERATION
   ✓ Critical alerts for equipment failure
   ✓ Warning alerts for anomalies
   ✓ Extensible for email/SMS/Slack integration

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## RUNNING BOTH BACKENDS SIMULTANEOUSLY

The ML Backend and Flask Backend work independently!
You can run both at the same time:

Terminal 1: Flask Backend (REST API + Data Storage)
─────────────────────────────────────────────────
$ cd /home/ravi/Machine-Guard-AI/backend
$ source ../venv/bin/activate
$ python app.py

Terminal 2: ML Backend (Real-time Predictions)
──────────────────────────────────────────────
$ cd /home/ravi/Machine-Guard-AI/ml_backend
$ source ../venv/bin/activate
$ python app.py

Both subscribe to the same MQTT broker and receive the same data!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## COMPARISON: ML Backend vs Flask Backend

┌────────────────────┬─────────────────────┬──────────────────────┐
│ Feature            │ ML Backend          │ Flask Backend        │
├────────────────────┼─────────────────────┼──────────────────────┤
│ MQTT Subscription  │ ✓ Direct            │ ✓ Direct             │
│ Data Storage       │ ❌ Not needed       │ ✓ Firebase/SQLite    │
│ Real-time Alerts   │ ✓ Instant           │ ⚠️ Delayed           │
│ Historical Data    │ ❌ No history       │ ✓ Full history       │
│ REST API           │ ❌ Not exposed      │ ✓ /api/sensors/*     │
│ Anomaly Detection  │ ✓ YES (this!)       │ ❌ No                │
│ Health Scoring     │ ✓ YES (this!)       │ ❌ No                │
│ Latency            │ ~1-2 seconds        │ ~2-3 seconds         │
│ Database Dependent │ ❌ No               │ ✓ Yes                │
│ Works Offline      │ ✓ Yes               │ ❌ No (needs MQTT)   │
└────────────────────┴─────────────────────┴──────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## EXAMPLE: Sensor Data Path

ESP32 Publishes:
────────────────
{
  "temperature": 26.5,
  "humidity": 45.2,
  "gas": 850,
  "vibration": 25,
  "current": 0.28
}

↓ Published to: iot/esp32/test (HiveMQ broker)

Flask Backend Receives:
───────────────────────
✓ Receives via MQTT
✓ Stores in Firebase
✓ Available via REST API (/api/sensors/latest)

ML Backend Receives (Simultaneously):
──────────────────────────────────
✓ Receives via MQTT
✓ Analyzes immediately
✓ Generates predictions
✓ Displays health report
✓ Creates alerts if needed

Both happen in parallel!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ADVANTAGES OF THIS APPROACH

✅ Real-time Processing
   - Data processed within 1-2 seconds
   - No delay from database operations

✅ Independent Operation
   - ML Backend works even if Flask/Firebase is down
   - ML doesn't depend on REST APIs

✅ Lower Costs
   - Reduced Firebase database writes
   - Direct MQTT subscription (no extra layer)

✅ Simple & Direct
   - Straightforward MQTT → ML pipeline
   - No complex database schemas needed

✅ Scalable
   - Can add multiple ML backends subscribed to same topic
   - Can subscribe to multiple MQTT topics

✅ Extensible
   - Easy to add custom detection rules
   - Easy to integrate email/SMS/Slack alerts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## NEXT STEPS

1. ✅ ML Backend Created
2. ✅ Dependencies Installed
3. 🔲 Run ML Backend: ./start.sh
4. 🔲 Monitor real-time predictions
5. 🔲 Customize detection rules (optional)
6. 🔲 Add alert integrations (email/SMS/Slack) (optional)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For detailed documentation, see:
📖 /home/ravi/Machine-Guard-AI/ml_backend/README.md

""")

# AutoForge IoT Backend

A production-ready Flask-based backend system for collecting real-time sensor data from ESP32 IoT devices via MQTT, storing data in a database, and exposing REST APIs for frontend dashboards.

## Overview

AutoForge Backend is designed to:

- **Receive real-time sensor data** from ESP32 devices via MQTT protocol
- **Validate and normalize** incoming payloads with comprehensive error handling
- **Store sensor readings** in a database with automatic schema creation
- **Expose REST APIs** for querying sensor data and device status
- **Prepare data for ML** with numpy-ready data export functionality
- **Handle failures gracefully** with automatic MQTT reconnection and thread-safe operations

## Features

- ✅ **MQTT Data Ingestion**: Subscribes to sensor topics, validates payloads, prevents crashes on malformed data
- ✅ **SQLAlchemy ORM**: Flexible database support (SQLite, PostgreSQL, MySQL)
- ✅ **REST APIs**: JSON endpoints for querying latest readings, history, and statistics
- ✅ **Structured Logging**: Colored console logs + rotating file logs
- ✅ **CORS Enabled**: Ready for frontend integration
- ✅ **Type Hints**: Full type annotations for better code quality
- ✅ **Environment Configuration**: 12-factor app principles with .env file support
- ✅ **ML-Ready Data Pipeline**: Numpy-compatible data format for future ML integration
- ✅ **Error Resilience**: Graceful handling of MQTT disconnections and invalid data

## Architecture

```
┌──────────────┐
│  ESP32       │
│  Devices     │
└──────┬───────┘
       │ (MQTT)
       ▼
┌──────────────────────────────────────┐
│  MQTT Broker (external)              │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  AutoForge Backend                   │
│  ┌────────────────────────────────┐  │
│  │ MQTT Client                    │  │
│  │ - Subscribe to sensors/#       │  │
│  │ - Validate payloads            │  │
│  │ - Extract device_id, metrics   │  │
│  └────────────┬───────────────────┘  │
│               │                       │
│  ┌────────────▼───────────────────┐  │
│  │ Database Layer (SQLAlchemy)    │  │
│  │ - SensorReading model          │  │
│  │ - Insert, Query, Aggregate     │  │
│  │ - ML data export               │  │
│  └────────────┬───────────────────┘  │
│               │                       │
│  ┌────────────▼───────────────────┐  │
│  │ Flask REST API                 │  │
│  │ GET  /api/health               │  │
│  │ GET  /api/sensors/latest       │  │
│  │ GET  /api/sensors/history      │  │
│  │ GET  /api/sensors/stats        │  │
│  │ GET  /api/sensors/ml-data      │  │
│  │ POST /api/control              │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Frontend Dashboard / ML Pipeline    │
│  (Consumes REST API)                 │
└──────────────────────────────────────┘
```

## Project Structure

```
backend/
├── app.py                 # Main Flask application entry point
├── config.py              # Environment variable configuration management
├── models.py              # SQLAlchemy ORM models (SensorReading)
├── database.py            # Database layer with CRUD operations
├── mqtt_client.py         # MQTT client with reconnection and validation
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── routes/
│   ├── sensors.py         # GET /api/sensors/* endpoints
│   ├── system.py          # GET /api/health endpoint
│   └── control.py         # POST /api/control endpoint
└── utils/
    └── logger.py          # Structured logging with colors
```

## Prerequisites

- **Python 3.9+**
- **MQTT Broker** (e.g., Mosquitto, HiveMQ, AWS IoT Core)
- **Database** (SQLite for development, PostgreSQL for production)
- **pip** (Python package manager)

## Installation

### 1. Clone the repository

```bash
cd /path/to/Machine-Guard-AI
```

### 2. Create a Python virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure environment variables

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your actual configuration:

```env
MQTT_BROKER=your-mqtt-broker.com
MQTT_PORT=1883
DATABASE_URL=sqlite:///sensors.db
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_ENV=production
LOG_LEVEL=INFO
```

#### Database URL Examples

- **SQLite** (Development): `sqlite:///sensors.db`
- **PostgreSQL** (Production): `postgresql://user:password@localhost:5432/autoforge`
- **MySQL**: `mysql+pymysql://user:password@localhost:3306/autoforge`

For PostgreSQL, install the driver:
```bash
pip install psycopg2-binary
```

### 5. Run the backend

```bash
cd backend
python app.py
```

You should see output like:
```
2026-01-29 14:30:45 - __main__ - INFO - ============================================================
2026-01-29 14:30:45 - __main__ - INFO - Initializing AutoForge IoT Backend
2026-01-29 14:30:45 - __main__ - INFO - ============================================================
2026-01-29 14:30:45 - __main__ - INFO - Configuration loaded: MQTT=mqtt.example.com:1883, Database=sqlite:///sensors.db
2026-01-29 14:30:45 - __main__ - INFO - Database initialized successfully
2026-01-29 14:30:45 - config - INFO - MQTT client connected
2026-01-29 14:30:45 - __main__ - INFO - ============================================================
2026-01-29 14:30:45 - __main__ - INFO - AutoForge Backend initialized successfully!
2026-01-29 14:30:45 - __main__ - INFO - ============================================================
2026-01-29 14:30:45 - __main__ - INFO - Starting Flask server on 0.0.0.0:5000
```

The API is now running at `http://localhost:5000`

## REST API Documentation

### Health Check

```http
GET /api/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "AutoForge IoT Backend",
  "version": "1.0.0"
}
```

---

### Get Latest Sensor Reading

```http
GET /api/sensors/latest?device_id=ESP32_001
```

**Query Parameters:**
- `device_id` (optional): Filter by specific device

**Response (200 OK):**
```json
{
  "data": {
    "id": 1,
    "device_id": "ESP32_001",
    "temperature": 24.5,
    "vibration": 12.3,
    "gas": 450.0,
    "power": 250.5,
    "timestamp": "2026-01-29T14:30:45",
    "created_at": "2026-01-29T14:30:46"
  }
}
```

**Response (404 Not Found):**
```json
{
  "message": "No sensor readings found",
  "device_id": "ESP32_001"
}
```

---

### Get Sensor History

```http
GET /api/sensors/history?device_id=ESP32_001&limit=100&offset=0
```

**Query Parameters:**
- `device_id` (optional): Filter by specific device
- `limit` (optional): Maximum records to return (1-10000, default: 100)
- `offset` (optional): Number of records to skip (default: 0)

**Response (200 OK):**
```json
{
  "count": 50,
  "limit": 100,
  "offset": 0,
  "device_id": "ESP32_001",
  "data": [
    {
      "id": 50,
      "device_id": "ESP32_001",
      "temperature": 24.5,
      "vibration": 12.3,
      "gas": 450.0,
      "power": 250.5,
      "timestamp": "2026-01-29T14:30:45",
      "created_at": "2026-01-29T14:30:46"
    },
    ...
  ]
}
```

---

### Get Sensor Statistics

```http
GET /api/sensors/stats?device_id=ESP32_001
```

**Query Parameters:**
- `device_id` (optional): Filter by specific device

**Response (200 OK):**
```json
{
  "stats": {
    "count": 1000,
    "avg_temperature": 23.8,
    "avg_vibration": 15.2,
    "avg_gas": 480.5,
    "avg_power": 245.3
  },
  "device_id": "ESP32_001"
}
```

---

### Get ML Pipeline Data

```http
GET /api/sensors/ml-data?device_id=ESP32_001&limit=1000
```

Returns sensor data in numpy-ready format for machine learning applications.

**Query Parameters:**
- `device_id` (optional): Filter by specific device
- `limit` (optional): Maximum records to retrieve (default: 1000)

**Response (200 OK):**
```json
{
  "sample_count": 500,
  "device_id": "ESP32_001",
  "data": {
    "timestamps": ["2026-01-29T14:30:45", "2026-01-29T14:31:45", ...],
    "temperatures": [24.5, 24.3, 24.7, ...],
    "vibrations": [12.3, 12.5, 12.1, ...],
    "gases": [450.0, 452.0, 448.0, ...],
    "powers": [250.5, 251.0, 249.5, ...],
    "device_ids": ["ESP32_001", "ESP32_001", ...]
  }
}
```

---

### Send Control Command (Placeholder)

```http
POST /api/control
Content-Type: application/json

{
  "device_id": "ESP32_001",
  "command": "restart",
  "parameters": {
    "delay_seconds": 5
  }
}
```

**Response (202 Accepted):**
```json
{
  "status": "acknowledged",
  "device_id": "ESP32_001",
  "command": "restart",
  "message": "Command will be sent to device (implementation pending)"
}
```

## MQTT Integration

### Expected Payload Format

Your ESP32 devices should publish JSON payloads with the following structure to the configured `SENSOR_TOPIC`:

```json
{
  "temperature": 24.5,
  "vibration": 12.3,
  "gas": 450.0,
  "power": 250.5,
  "timestamp": "2026-01-29T14:30:45.123456"
}
```

Or using Unix epoch timestamp:

```json
{
  "temperature": 24.5,
  "vibration": 12.3,
  "gas": 450.0,
  "power": 250.5,
  "timestamp": 1706539845.123456
}
```

### Topic Structure

- **Sensor Data**: `sensors/{device_id}/data`
  - Device ID is extracted from the topic
  - Example: `sensors/ESP32_001/data`

- **Control Messages**: `control/{device_id}/command`
  - Future implementation for device control

### Validation Rules

- All required fields must be present: `temperature`, `vibration`, `gas`, `power`, `timestamp`
- All numeric fields are converted to float
- Malformed payloads are logged but **do not crash** the application
- Missing fields are detected and logged as warnings
- Type conversion errors (e.g., "abc" for temperature) are logged and skipped

## Data Model

### SensorReading Table

```
Column          | Type      | Description
────────────────|───────────|─────────────────────────────────────
id              | Integer   | Auto-incrementing primary key
device_id       | String    | Device identifier (indexed)
temperature     | Float     | Temperature in Celsius
vibration       | Float     | Vibration measurement
gas             | Float     | Gas sensor reading (e.g., CO2 ppm)
power           | Float     | Power consumption in watts
timestamp       | DateTime  | Device-reported timestamp (indexed)
created_at      | DateTime  | Server-side timestamp, auto-filled (indexed)
```

**Indexes**: `device_id`, `timestamp`, `created_at` for fast queries

## Configuration Reference

### Environment Variables

```env
# MQTT Configuration
MQTT_BROKER          # Hostname/IP of MQTT broker (required)
MQTT_PORT            # MQTT broker port (default: 1883)
SENSOR_TOPIC         # Topic pattern for sensor subscriptions (default: sensors/+/data)
CONTROL_TOPIC        # Topic pattern for control messages (default: control/+/command)

# Database
DATABASE_URL         # SQLAlchemy connection string (required)

# Flask Server
FLASK_HOST           # Bind address (default: 0.0.0.0)
FLASK_PORT           # Server port (default: 5000)
FLASK_ENV            # Environment: development or production (default: production)

# Logging
LOG_LEVEL            # DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
```

## Logging

Logs are output to:
1. **Console**: Colored output for development
2. **File**: Rotating log files (max 10 MB per file, keep 5 backups)

Log files are stored in the current working directory:
- Default log file: `autoforge.log`

### Log Levels

- **DEBUG**: Detailed diagnostic information (MQTT messages, database queries)
- **INFO**: General information (connections, data ingestion)
- **WARNING**: Warning messages (malformed payloads, missing fields)
- **ERROR**: Error conditions (database failures, connection errors)
- **CRITICAL**: Critical errors (initialization failures)

## Performance Considerations

- **Database**: Uses connection pooling with pre-ping for reliability
- **MQTT**: Non-blocking network loop in background thread
- **Threading**: Flask app and MQTT loop run in separate threads safely
- **Pagination**: History endpoint supports limit/offset for large datasets
- **Indexes**: Database indexes on frequently queried columns (device_id, timestamp)

## Error Handling

### MQTT Disconnection
- Automatic reconnection with exponential backoff (5s → 120s)
- Logged as warnings, does not crash the application
- Connection status available via health check

### Malformed Payloads
- Invalid JSON: Logged as warning, message skipped
- Missing required fields: Logged as warning, message skipped
- Type conversion errors: Logged as warning, message skipped
- **Result**: Backend continues operating normally

### Database Errors
- Connection failures logged and handled gracefully
- Query errors logged with details
- API returns 500 errors with generic message to client

## Development Tips

### Testing MQTT Integration

1. **Install MQTT CLI tool**:
   ```bash
   brew install mqtt-cli  # macOS
   apt install mosquitto-clients  # Linux
   ```

2. **Publish test data**:
   ```bash
   mosquitto_pub -h <broker> -t sensors/ESP32_001/data -m '{
     "temperature": 24.5,
     "vibration": 12.3,
     "gas": 450.0,
     "power": 250.5,
     "timestamp": "2026-01-29T14:30:45"
   }'
   ```

3. **Query the API**:
   ```bash
   curl http://localhost:5000/api/sensors/latest?device_id=ESP32_001
   ```

### Local Testing with Mosquitto

Start a local MQTT broker:
```bash
docker run -it -p 1883:1883 eclipse-mosquitto:latest
```

Then update `.env`:
```env
MQTT_BROKER=localhost
MQTT_PORT=1883
```

### Debugging

Set log level to DEBUG:
```env
LOG_LEVEL=DEBUG
```

This will show all MQTT messages and database queries.

## Production Deployment

### Database Setup

For PostgreSQL:
```bash
createdb autoforge
# Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@host:5432/autoforge
```

### WSGI Server (Production)

Replace the development Flask server with Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

ENV FLASK_ENV=production
EXPOSE 5000

CMD ["python", "app.py"]
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name api.autoforge.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Future Enhancements

The backend is designed to support future additions:

1. **Machine Learning Pipeline** (data ready via `/api/sensors/ml-data`)
2. **Device Control** (POST `/api/control` awaiting MQTT publish implementation)
3. **Real-time WebSocket** (for live dashboard updates)
4. **Data Aggregation** (hourly/daily summaries)
5. **Alerts & Anomaly Detection** (threshold-based notifications)
6. **Authentication** (JWT tokens for API security)
7. **Multi-tenancy** (support for multiple organizations)

## Troubleshooting

### MQTT Connection Failed
```
Error: Failed to initialize MQTT client: Temporary failure in name resolution
```
**Solution**: Verify `MQTT_BROKER` is reachable from your network

### Database Connection Error
```
Error: Failed to initialize database: could not connect to server
```
**Solution**: Check `DATABASE_URL` format and database server is running

### No Data in API
1. Check MQTT broker is running
2. Verify ESP32 devices are connected and publishing
3. Check logs: `tail -f autoforge.log`
4. Test with `mosquitto_pub` to manually publish data

### Port Already in Use
```
OSError: [Errno 48] Address already in use
```
**Solution**: Change `FLASK_PORT` in `.env` or kill existing process:
```bash
lsof -ti:5000 | xargs kill -9
```

## Code Quality

- **Type Hints**: Full type annotations for better IDE support and type checking
- **Docstrings**: All public functions have detailed docstrings (Google style)
- **PEP 8**: Code formatted with 100-character line length
- **Error Messages**: Clear, actionable error messages in logs
- **No Hardcoded Secrets**: All configuration via environment variables

## License

[Specify your license]

## Support

For issues, questions, or contributions:
- GitHub Issues: [Link to repository]
- Email: [Support email]

---

**AutoForge** - Production-Ready IoT Backend for ESP32 Sensor Networks

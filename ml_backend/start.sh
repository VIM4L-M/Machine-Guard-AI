#!/bin/bash
# ML Backend Quick Start Script

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Machine-Guard ML Backend - Quick Start                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if venv is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "📦 Activating virtual environment..."
    source ../venv/bin/activate
fi

echo "✓ Virtual environment activated"
echo ""

# Check if dependencies are installed
echo "📦 Checking dependencies..."
pip list | grep -q paho-mqtt && echo "✓ paho-mqtt installed" || pip install paho-mqtt==2.1.0
pip list | grep -q python-dotenv && echo "✓ python-dotenv installed" || pip install python-dotenv==1.0.0
pip list | grep -q numpy && echo "✓ numpy installed" || pip install "numpy>=2.0.0"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Configuration Check                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check .env file
if [ -f .env ]; then
    echo "✓ .env file found"
    echo ""
    echo "Current MQTT Configuration:"
    grep "MQTT" .env
else
    echo "❌ .env file not found"
    echo "Creating default .env..."
    cat > .env << 'EOF'
# MQTT Configuration
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883
MQTT_TOPIC=iot/esp32/test
EOF
    echo "✓ Created .env with default values"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              Starting ML Backend                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Connecting to MQTT broker..."
echo "🤖 Starting real-time anomaly detection..."
echo ""
echo "Press Ctrl+C to stop the backend"
echo ""

# Start the ML backend
python app.py

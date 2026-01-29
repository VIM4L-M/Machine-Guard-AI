#!/usr/bin/env python3
"""
AutoForge Backend - Quick Start Script
This script sets up and runs the backend with example MQTT data simulation.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

def print_section(title: str) -> None:
    """Print formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")

def check_requirements() -> bool:
    """Check if required dependencies are installed."""
    print_section("Checking Requirements")
    
    try:
        import flask
        import flask_cors
        import paho.mqtt.client
        import sqlalchemy
        print("✓ All Python dependencies found")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {str(e)}")
        print("\nInstall dependencies with:")
        print("  pip install -r backend/requirements.txt")
        return False

def check_environment() -> bool:
    """Check if .env file exists."""
    print_section("Checking Environment Configuration")
    
    env_file = Path("backend/.env")
    if env_file.exists():
        print("✓ .env file found")
        return True
    else:
        print("✗ .env file not found")
        print("\nCreate it from the template:")
        print("  cp backend/.env.example backend/.env")
        print("\nThen edit backend/.env with your configuration")
        return False

def print_quick_start() -> None:
    """Print quick start instructions."""
    print_section("Quick Start Guide")
    
    instructions = """
1. INSTALL DEPENDENCIES
   pip install -r backend/requirements.txt

2. CONFIGURE ENVIRONMENT
   cp backend/.env.example backend/.env
   # Edit backend/.env with your MQTT broker details

3. RUN THE BACKEND
   cd backend
   python app.py

4. TEST THE API
   # In another terminal:
   curl http://localhost:5000/api/health

5. SEND TEST DATA VIA MQTT
   mosquitto_pub -h <your-mqtt-broker> -t sensors/ESP32_001/data -m '{
     "temperature": 24.5,
     "vibration": 12.3,
     "gas": 450.0,
     "power": 250.5,
     "timestamp": "2026-01-29T14:30:45"
   }'

6. QUERY SENSOR DATA
   curl http://localhost:5000/api/sensors/latest?device_id=ESP32_001
   curl http://localhost:5000/api/sensors/history?limit=10
   curl http://localhost:5000/api/sensors/stats

MORE INFORMATION
   See backend/README.md for complete documentation
"""
    
    print(instructions)

def main() -> int:
    """Main entry point."""
    print("\n" + "=" * 70)
    print("  AutoForge IoT Backend - Setup Assistant")
    print("=" * 70)
    
    # Change to backend directory
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("\n✗ Error: backend directory not found")
        print("Run this script from the project root directory")
        return 1
    
    # Check requirements
    if not check_requirements():
        return 1
    
    # Check environment
    if not check_environment():
        return 1
    
    # Print quick start
    print_quick_start()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

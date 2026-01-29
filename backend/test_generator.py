#!/usr/bin/env python3
"""
Test Data Generator for AutoForge Backend
Simulates ESP32 devices publishing sensor data via MQTT.
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: paho-mqtt is required")
    print("Install with: pip install paho-mqtt")
    sys.exit(1)


class TestDataGenerator:
    """Simulates IoT devices publishing sensor data."""

    def __init__(self, broker: str, port: int, device_id: str = "ESP32_001"):
        """
        Initialize the test data generator.

        Args:
            broker: MQTT broker hostname
            port: MQTT broker port
            device_id: Device identifier to use
        """
        self.broker = broker
        self.port = port
        self.device_id = device_id
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.running = False

    def _on_connect(self, client, userdata, connect_flags, rc, properties):
        """Handle connection."""
        if rc == 0:
            print(f"✓ Connected to MQTT broker {self.broker}:{self.port}")
            self.running = True
        else:
            print(f"✗ Failed to connect (code {rc})")
            self.running = False

    def _on_disconnect(self, client, userdata, disconnect_flags, rc, properties):
        """Handle disconnection."""
        self.running = False
        if rc != 0:
            print(f"Unexpected disconnection (code {rc})")

    def generate_sensor_data(self) -> dict:
        """
        Generate realistic sensor data with some variation.

        Returns:
            Dictionary with sensor readings
        """
        # Base values with small variations to simulate real data
        base_temp = 24.0
        base_vibration = 10.0
        base_gas = 400.0
        base_power = 240.0

        return {
            "temperature": round(base_temp + random.uniform(-2, 2), 2),
            "vibration": round(base_vibration + random.uniform(-5, 5), 2),
            "gas": round(base_gas + random.uniform(-50, 50), 2),
            "power": round(base_power + random.uniform(-20, 20), 2),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            time.sleep(1)  # Wait for connection
        except Exception as e:
            print(f"✗ Connection error: {str(e)}")
            raise

    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def publish_data(self, count: int = 10, interval: float = 1.0):
        """
        Publish sensor data to MQTT.

        Args:
            count: Number of messages to publish
            interval: Interval between messages in seconds
        """
        if not self.running:
            print("✗ Not connected to MQTT broker")
            return

        topic = f"sensors/{self.device_id}/data"
        print(f"\nPublishing to topic: {topic}\n")

        for i in range(count):
            data = self.generate_sensor_data()
            payload = json.dumps(data)

            result = self.client.publish(topic, payload)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(
                    f"  [{i + 1}/{count}] Published: "
                    f"temp={data['temperature']}°C, "
                    f"vib={data['vibration']}, "
                    f"gas={data['gas']} ppm"
                )
            else:
                print(f"  [{i + 1}/{count}] ✗ Failed to publish (code {result.rc})")

            if i < count - 1:
                time.sleep(interval)

        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AutoForge Test Data Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Publish 10 messages to local broker
  python backend/test_generator.py

  # Publish 100 messages to remote broker
  python backend/test_generator.py --broker mqtt.example.com --count 100

  # Publish messages from multiple devices
  for device in ESP32_001 ESP32_002 ESP32_003; do
    python backend/test_generator.py --device-id "$device" &
  done
        """,
    )

    parser.add_argument(
        "--broker",
        default="localhost",
        help="MQTT broker hostname (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=1883,
        help="MQTT broker port (default: 1883)",
    )
    parser.add_argument(
        "--device-id",
        default="ESP32_001",
        help="Device identifier (default: ESP32_001)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of messages to publish (default: 10)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Interval between messages in seconds (default: 1.0)",
    )

    args = parser.parse_args()

    print(f"\n{'=' * 70}")
    print(f"  AutoForge Test Data Generator")
    print(f"{'=' * 70}\n")
    print(f"Broker:   {args.broker}:{args.port}")
    print(f"Device:   {args.device_id}")
    print(f"Messages: {args.count}")
    print(f"Interval: {args.interval}s\n")

    generator = TestDataGenerator(args.broker, args.port, args.device_id)

    try:
        generator.connect()
        generator.publish_data(count=args.count, interval=args.interval)
        print("✓ Test data published successfully")
        return 0
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 0
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return 1
    finally:
        generator.disconnect()


if __name__ == "__main__":
    sys.exit(main())

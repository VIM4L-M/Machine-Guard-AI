"""
ML Backend for Machine-Guard
Subscribes directly to MQTT broker for real-time sensor data
"""

import json
import os
from datetime import datetime
from typing import Callable, Optional

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MLMQTTClient:
    """
    MQTT client for ML backend to receive real-time sensor data.
    
    Connects to MQTT broker and processes sensor readings for ML predictions.
    """

    def __init__(
        self,
        broker: str = "broker.hivemq.com",
        port: int = 1883,
        sensor_topic: str = "iot/esp32/test",
        on_data_callback: Optional[Callable] = None,
    ):
        """
        Initialize ML MQTT client.

        Args:
            broker: MQTT broker hostname/IP (default: HiveMQ public broker)
            port: MQTT broker port (default: 1883)
            sensor_topic: Topic to subscribe to (default: iot/esp32/test)
            on_data_callback: Callback function when data is received
        """
        self.broker = broker
        self.port = port
        self.sensor_topic = sensor_topic
        self.on_data_callback = on_data_callback

        # Create MQTT client
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.connected = False
        self.data_buffer = []  # Store recent readings for batch processing

    def _on_connect(self, client, userdata, connect_flags, reason_code, properties):
        """Handle connection to MQTT broker."""
        if reason_code == 0:
            print(f"✓ Connected to MQTT broker: {self.broker}:{self.port}")
            # Subscribe to sensor topic
            self.client.subscribe(self.sensor_topic)
            print(f"✓ Subscribed to topic: {self.sensor_topic}")
            self.connected = True
        else:
            print(f"❌ Connection failed with code: {reason_code}")
            self.connected = False

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        """Handle disconnection from MQTT broker."""
        self.connected = False
        if reason_code != 0:
            print(f"⚠️  Unexpected MQTT disconnection with code: {reason_code}")
        else:
            print("✓ Cleanly disconnected from MQTT broker")

    def _on_message(self, client, userdata, msg):
        """
        Handle incoming MQTT messages.
        
        Args:
            client: MQTT client instance
            userdata: User data
            msg: MQTT message object
        """
        try:
            # Decode JSON payload
            payload = json.loads(msg.payload.decode("utf-8"))
            
            # Add timestamp if not present
            if "timestamp" not in payload:
                payload["timestamp"] = datetime.utcnow().isoformat()
            
            print(f"📊 Received sensor data: {payload}")
            
            # Store in buffer for batch processing
            self.data_buffer.append(payload)
            
            # Call custom callback if provided
            if self.on_data_callback:
                self.on_data_callback(payload)
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON received: {str(e)}")
        except Exception as e:
            print(f"❌ Error processing message: {str(e)}")

    def connect(self):
        """Connect to MQTT broker and start listening."""
        try:
            print(f"🔄 Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()  # Start background thread
            print("✓ MQTT client loop started")
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")

    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def get_latest_readings(self, count: int = 10) -> list:
        """
        Get the latest N readings from buffer.
        
        Args:
            count: Number of latest readings to return
            
        Returns:
            List of sensor readings
        """
        return self.data_buffer[-count:] if self.data_buffer else []

    def clear_buffer(self):
        """Clear the data buffer."""
        self.data_buffer.clear()


if __name__ == "__main__":
    # Example usage
    
    def custom_callback(data):
        """Custom callback to process sensor data."""
        print(f"🤖 ML Processing: temp={data.get('temperature')}°C, "
              f"humidity={data.get('humidity')}%, gas={data.get('gas')}")
    
    # Create MQTT client
    mqtt_client = MLMQTTClient(
        broker=os.getenv("MQTT_BROKER", "broker.hivemq.com"),
        port=int(os.getenv("MQTT_PORT", 1883)),
        sensor_topic=os.getenv("MQTT_TOPIC", "iot/esp32/test"),
        on_data_callback=custom_callback,
    )
    
    # Connect and start receiving data
    mqtt_client.connect()
    
    try:
        # Keep the script running
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        mqtt_client.disconnect()

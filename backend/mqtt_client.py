"""
MQTT client for Machine-Guard backend.
Handles connection, subscription, and data validation from IoT devices.
"""

import json
import threading
import time
from datetime import datetime
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from utils.logger import setup_logger

logger = setup_logger(__name__)


class MQTTClient:
    """
    MQTT client for receiving sensor data from IoT devices.

    Connects to an MQTT broker, subscribes to sensor topics, validates payloads,
    and forwards data to a callback function for storage.
    """

    REQUIRED_FIELDS = {"temperature", "humidity", "gas", "current"}

    def __init__(
        self,
        broker: str,
        port: int,
        sensor_topic: str,
        control_topic: str,
        on_message_callback: Callable[[dict], None],
    ) -> None:
        """
        Initialize MQTT client.

        Args:
            broker: MQTT broker hostname/IP
            port: MQTT broker port
            sensor_topic: Topic pattern to subscribe for sensor data (e.g., "sensors/+/data")
            control_topic: Topic pattern for control messages
            on_message_callback: Callback function to handle validated sensor data
                Called with dict containing device_id, temperature, vibration, gas, power, timestamp

        Raises:
            ValueError: If callback is not callable
        """
        if not callable(on_message_callback):
            raise ValueError("on_message_callback must be callable")

        self.broker = broker
        self.port = port
        self.sensor_topic = sensor_topic
        self.control_topic = control_topic
        self.on_message_callback = on_message_callback

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_log = self._on_log

        self.connected = False
        self._reconnect_delay = 5  # Start with 5 seconds
        self._max_reconnect_delay = 120  # Max 2 minutes

    def connect(self) -> None:
        """
        Connect to MQTT broker with automatic reconnection.

        Starts the network loop in a background thread for non-blocking operation.
        """
        try:
            logger.info(f"Connecting to MQTT broker: {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()  # Start background thread for network loop
            logger.info("MQTT client loop started")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {str(e)}")
            raise

    def disconnect(self) -> None:
        """Disconnect from MQTT broker and stop network loop."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
        except Exception as e:
            logger.error(f"Error during MQTT disconnect: {str(e)}")

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: any,
        connect_flags: dict,
        rc: int,
        properties: any,
    ) -> None:
        """Handle MQTT connection callback."""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            self.connected = True
            self._reconnect_delay = 5  # Reset reconnection delay on success

            # Subscribe to sensor and control topics
            self.client.subscribe(self.sensor_topic)
            self.client.subscribe(self.control_topic)
            logger.info(f"Subscribed to topics: {self.sensor_topic}, {self.control_topic}")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
            self.connected = False

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: any,
        disconnect_flags: dict,
        rc: int,
        properties: any,
    ) -> None:
        """Handle MQTT disconnection callback."""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection with code {rc}")
            self._attempt_reconnect()
        else:
            logger.info("Cleanly disconnected from MQTT broker")

    def _attempt_reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        logger.info(
            f"Attempting to reconnect in {self._reconnect_delay} seconds..."
        )
        time.sleep(self._reconnect_delay)
        try:
            self.client.reconnect()
            self._reconnect_delay = 5  # Reset on successful reconnect
        except Exception as e:
            logger.error(f"Reconnection failed: {str(e)}")
            # Increase delay for next attempt (exponential backoff)
            self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)

    def _on_log(
        self,
        client: mqtt.Client,
        userdata: any,
        level: int,
        buf: str,
    ) -> None:
        """Handle MQTT library log messages (debug level)."""
        if level == mqtt.MQTT_LOG_DEBUG:
            logger.debug(f"MQTT: {buf}")

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """
        Handle incoming MQTT messages.

        Validates payload format and required fields before forwarding to callback.
        Malformed messages are logged but do not crash the application.
        """
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            logger.debug(f"Received message on {msg.topic}: {payload}")

            # Validate required fields
            if not self.REQUIRED_FIELDS.issubset(payload.keys()):
                missing_fields = self.REQUIRED_FIELDS - set(payload.keys())
                logger.warning(
                    f"Malformed payload on {msg.topic}: missing fields {missing_fields}"
                )
                return

            # Convert values to float safely
            try:
                data = {
                    "device_id": self._extract_device_id(msg.topic),
                    "temperature": float(payload["temperature"]),
                    "humidity": float(payload["humidity"]),
                    "vibration": float(payload.get("vibration", 0)),  # Default to 0 if not present
                    "gas": float(payload["gas"]),
                    "power": float(payload.get("current", 0)),  # Map 'current' to 'power'
                    "timestamp": self._parse_timestamp(payload.get("timestamp")),
                }
            except (ValueError, TypeError) as e:
                logger.warning(f"Type conversion error on {msg.topic}: {str(e)}")
                return

            # Forward validated data to database layer
            self.on_message_callback(data)

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON on {msg.topic}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing message on {msg.topic}: {str(e)}")

    @staticmethod
    def _extract_device_id(topic: str) -> str:
        """
        Extract device ID from topic pattern.

        Expected topic format: sensors/{device_id}/data
        Falls back to full topic if pattern doesn't match.

        Args:
            topic: MQTT topic string

        Returns:
            Extracted device ID or full topic as fallback
        """
        parts = topic.split("/")
        if len(parts) >= 2:
            return parts[1]
        return topic

    @staticmethod
    def _parse_timestamp(timestamp_value: any) -> datetime:
        """
        Parse timestamp from various formats.

        If no timestamp provided, uses current UTC time.
        Supports ISO format strings and Unix epoch timestamps.

        Args:
            timestamp_value: Timestamp in ISO format, Unix epoch, or None

        Returns:
            datetime object in UTC
        """
        if timestamp_value is None:
            # No timestamp provided, use current time
            return datetime.utcnow()
        elif isinstance(timestamp_value, (int, float)):
            # Unix epoch timestamp
            return datetime.utcfromtimestamp(timestamp_value)
        elif isinstance(timestamp_value, str):
            # ISO format string
            try:
                return datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
            except ValueError:
                # Try Unix epoch as string
                return datetime.utcfromtimestamp(float(timestamp_value))
        else:
            # Fallback to current time
            return datetime.utcnow()

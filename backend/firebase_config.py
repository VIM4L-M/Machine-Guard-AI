"""
Firebase configuration and initialization for Machine-Guard backend.
"""

import os
import json
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, db

from utils.logger import setup_logger

logger = setup_logger(__name__)


class FirebaseDB:
    """Firebase Realtime Database manager for sensor readings."""

    def __init__(self, credentials_path: str, database_url: str) -> None:
        """
        Initialize Firebase connection.

        Args:
            credentials_path: Path to Firebase service account JSON file
            database_url: Firebase Realtime Database URL
                (e.g., "https://your-project.firebaseio.com")

        Raises:
            FileNotFoundError: If credentials file not found
            Exception: If Firebase initialization fails
        """
        self.credentials_path = credentials_path
        self.database_url = database_url

        try:
            # Check if credentials file exists
            if not Path(credentials_path).exists():
                raise FileNotFoundError(
                    f"Firebase credentials file not found: {credentials_path}\n"
                    "Download from: Firebase Console → Project Settings → Service Accounts"
                )

            # Initialize Firebase
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(
                cred,
                {"databaseURL": database_url}
            )

            self.db = db.reference()
            logger.info(f"Firebase Realtime Database connected: {database_url}")

        except FileNotFoundError as e:
            logger.error(str(e))
            raise
        except Exception as e:
            logger.error(f"Firebase initialization failed: {str(e)}")
            raise

    def insert_reading(self, reading_data: dict) -> dict:
        """
        Insert a sensor reading into Firebase.

        Args:
            reading_data: Dictionary with keys:
                - device_id: Device identifier
                - temperature: Temperature value (float)
                - vibration: Vibration value (float)
                - gas: Gas sensor value (float)
                - power: Power consumption (float)
                - timestamp: Device timestamp (datetime or string)

        Returns:
            Dictionary with reading data including Firebase key

        Raises:
            Exception: If database write fails
        """
        try:
            # Convert timestamp to ISO format string if datetime object
            from datetime import datetime
            if isinstance(reading_data.get("timestamp"), datetime):
                reading_data["timestamp"] = reading_data["timestamp"].isoformat()

            # Store reading in Firebase
            # Path: /sensor_readings/{device_id}/{timestamp_key}
            device_id = reading_data["device_id"]
            sensor_ref = self.db.child("sensor_readings").child(device_id)

            # Push creates a unique key and returns the new reference
            new_ref = sensor_ref.push(reading_data)

            logger.debug(
                f"Inserted reading: device={device_id}, "
                f"temp={reading_data.get('temperature')}°C, "
                f"humidity={reading_data.get('humidity')}%"
            )

            return {
                "key": new_ref.key,
                **reading_data
            }

        except Exception as e:
            logger.error(f"Failed to insert reading: {str(e)}")
            raise

    def get_latest_reading(self, device_id: str = None) -> dict:
        """
        Get the latest sensor reading.

        Args:
            device_id: Optional device ID to filter by

        Returns:
            Latest sensor reading or None if not found
        """
        try:
            if device_id:
                # Get latest reading for specific device
                readings_ref = self.db.child("sensor_readings").child(device_id)
            else:
                # Get latest from all devices
                readings_ref = self.db.child("sensor_readings")

            data = readings_ref.order_by_child("timestamp").limit_to_last(1).get()

            if data.val():
                # Extract the reading (could be nested by device_id)
                readings = data.val()
                if isinstance(readings, dict):
                    # Get last item
                    for key, value in reversed(list(readings.items())):
                        if isinstance(value, dict):
                            value["id"] = key
                            return value
            return None

        except Exception as e:
            logger.error(f"Failed to get latest reading: {str(e)}")
            return None

    def get_readings_history(
        self,
        device_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[list, int]:
        """
        Get historical sensor readings.

        Args:
            device_id: Optional device ID to filter by
            limit: Maximum records to return (max: 10000)
            offset: Number of records to skip

        Returns:
            Tuple of (readings list, total count)
        """
        try:
            limit = min(max(limit, 1), 10000)  # Clamp limit

            if device_id:
                readings_ref = self.db.child("sensor_readings").child(device_id)
            else:
                readings_ref = self.db.child("sensor_readings")

            data = readings_ref.order_by_child("timestamp").limit_to_last(limit + offset).get()

            readings = []
            if data.val():
                for key, value in data.val().items():
                    if isinstance(value, dict):
                        value["id"] = key
                        readings.append(value)

            # Apply offset by slicing from end
            readings = readings[-(limit):]  # Get last 'limit' items
            readings.reverse()  # Most recent first

            return readings, len(readings)

        except Exception as e:
            logger.error(f"Failed to get readings history: {str(e)}")
            return [], 0

    def get_device_list(self) -> list:
        """
        Get list of all devices that have sent data.

        Returns:
            List of device IDs
        """
        try:
            readings_ref = self.db.child("sensor_readings")
            data = readings_ref.get()

            if data.val():
                return list(data.val().keys())
            return []

        except Exception as e:
            logger.error(f"Failed to get device list: {str(e)}")
            return []

    def get_device_stats(self, device_id: str) -> dict:
        """
        Get statistics for a specific device.

        Args:
            device_id: Device identifier

        Returns:
            Dictionary with device statistics
        """
        try:
            readings_ref = self.db.child("sensor_readings").child(device_id)
            data = readings_ref.get()

            if not data.val():
                return {}

            readings = list(data.val().values())
            if not readings:
                return {}

            temps = [r.get("temperature", 0) for r in readings if isinstance(r, dict)]
            gases = [r.get("gas", 0) for r in readings if isinstance(r, dict)]

            return {
                "device_id": device_id,
                "total_readings": len(readings),
                "temp_avg": sum(temps) / len(temps) if temps else 0,
                "temp_min": min(temps) if temps else 0,
                "temp_max": max(temps) if temps else 0,
                "gas_avg": sum(gases) / len(gases) if gases else 0,
            }

        except Exception as e:
            logger.error(f"Failed to get device stats: {str(e)}")
            return {}

    def delete_old_readings(self, days: int = 30) -> int:
        """
        Delete readings older than specified days.

        Args:
            days: Delete readings older than this many days

        Returns:
            Number of readings deleted
        """
        try:
            from datetime import datetime, timedelta
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            readings_ref = self.db.child("sensor_readings")
            data = readings_ref.get()

            deleted_count = 0
            if data.val():
                for device_id, device_readings in data.val().items():
                    for key, reading in device_readings.items():
                        if isinstance(reading, dict):
                            if reading.get("timestamp", "") < cutoff_date:
                                self.db.child("sensor_readings").child(device_id).child(key).delete()
                                deleted_count += 1

            logger.info(f"Deleted {deleted_count} old readings (older than {days} days)")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete old readings: {str(e)}")
            return 0

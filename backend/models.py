"""
SQLAlchemy ORM models for Machine-Guard sensor data.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SensorReading(Base):
    """
    ORM model for sensor readings from IoT devices.

    Attributes:
        id: Unique identifier (auto-incremented)
        device_id: Device identifier (e.g., ESP32 MAC address)
        temperature: Temperature reading in Celsius
        humidity: Humidity reading in percentage
        vibration: Vibration level (0-100 or raw value)
        gas: Gas sensor reading (e.g., CO2 ppm)
        power: Power consumption in watts
        timestamp: Timestamp from the device (ISO format or epoch)
        created_at: Server-side creation timestamp (UTC)
    """

    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(50), nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    vibration = Column(Float, nullable=False)
    gas = Column(Float, nullable=False)
    power = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        """String representation of SensorReading."""
        return (
            f"<SensorReading(id={self.id}, device_id={self.device_id}, "
            f"temperature={self.temperature}, humidity={self.humidity}, "
            f"vibration={self.vibration}, gas={self.gas}, power={self.power}, "
            f"timestamp={self.timestamp})>"
        )

    def to_dict(self) -> dict:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of the sensor reading
        """
        return {
            "id": self.id,
            "device_id": self.device_id,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "vibration": self.vibration,
            "gas": self.gas,
            "power": self.power,
            "timestamp": self.timestamp.isoformat(),
            "created_at": self.created_at.isoformat(),
        }

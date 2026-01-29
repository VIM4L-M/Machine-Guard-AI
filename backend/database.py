"""
Database layer for Machine-Guard backend.
Handles SQLAlchemy session management and data persistence.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from models import Base, SensorReading
from utils.logger import setup_logger

logger = setup_logger(__name__)


class Database:
    """Database manager for sensor readings."""

    def __init__(self, database_url: str) -> None:
        """
        Initialize database connection and create tables.

        Args:
            database_url: SQLAlchemy database URL
                (e.g., 'sqlite:///sensors.db' or 'postgresql://user:pass@host/db')

        Raises:
            SQLAlchemyError: If database connection fails
        """
        try:
            self.engine = create_engine(
                database_url,
                pool_pre_ping=True,  # Verify connections before using
                echo=False,  # Set to True for SQL debug logs
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
            )
            self._create_tables()
            logger.info(f"Database initialized: {database_url}")
        except SQLAlchemyError as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

    def _create_tables(self) -> None:
        """Create all tables defined in ORM models."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created/verified")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy Session instance
        """
        return self.SessionLocal()

    def insert_reading(self, reading_data: dict) -> Optional[SensorReading]:
        """
        Insert a sensor reading into the database.

        Args:
            reading_data: Dictionary with keys:
                - device_id: Device identifier
                - temperature: Temperature value (float)
                - humidity: Humidity value (float)
                - vibration: Vibration value (float)
                - gas: Gas sensor value (float)
                - power: Power consumption (float)
                - timestamp: Device timestamp (datetime)

        Returns:
            Created SensorReading instance, or None if insertion fails

        Raises:
            KeyError: If required fields are missing
        """
        session = self.get_session()
        try:
            reading = SensorReading(
                device_id=reading_data["device_id"],
                temperature=reading_data["temperature"],
                humidity=reading_data["humidity"],
                vibration=reading_data["vibration"],
                gas=reading_data["gas"],
                power=reading_data["power"],
                timestamp=reading_data["timestamp"],
            )
            session.add(reading)
            session.commit()
            logger.debug(
                f"Inserted reading: device={reading.device_id}, "
                f"temp={reading.temperature}°C, humidity={reading.humidity}%"
            )
            return reading
        except (SQLAlchemyError, KeyError) as e:
            session.rollback()
            logger.error(f"Failed to insert sensor reading: {str(e)}")
            return None
        finally:
            session.close()

    def get_latest_reading(
        self, device_id: Optional[str] = None
    ) -> Optional[SensorReading]:
        """
        Get the latest sensor reading.

        Args:
            device_id: Optional device ID to filter by specific device

        Returns:
            Latest SensorReading instance, or None if no records exist
        """
        session = self.get_session()
        try:
            query = session.query(SensorReading).order_by(
                SensorReading.created_at.desc()
            )
            if device_id:
                query = query.filter(SensorReading.device_id == device_id)
            reading = query.first()
            return reading
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch latest reading: {str(e)}")
            return None
        finally:
            session.close()

    def get_history(
        self,
        device_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SensorReading]:
        """
        Get historical sensor readings.

        Args:
            device_id: Optional device ID to filter by specific device
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of SensorReading instances
        """
        session = self.get_session()
        try:
            query = session.query(SensorReading).order_by(
                SensorReading.created_at.desc()
            )
            if device_id:
                query = query.filter(SensorReading.device_id == device_id)
            readings = query.limit(limit).offset(offset).all()
            return readings if readings else []
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch history: {str(e)}")
            return []
        finally:
            session.close()

    def get_stats(
        self,
        device_id: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Get aggregated statistics for sensor readings.

        Args:
            device_id: Optional device ID to filter by specific device

        Returns:
            Dictionary with count, avg_temperature, avg_vibration, avg_gas, avg_power
            or None if query fails
        """
        session = self.get_session()
        try:
            from sqlalchemy import func

            query = session.query(
                func.count(SensorReading.id).label("count"),
                func.avg(SensorReading.temperature).label("avg_temperature"),
                func.avg(SensorReading.vibration).label("avg_vibration"),
                func.avg(SensorReading.gas).label("avg_gas"),
                func.avg(SensorReading.power).label("avg_power"),
            )
            if device_id:
                query = query.filter(SensorReading.device_id == device_id)

            result = query.first()
            if result:
                return {
                    "count": result.count or 0,
                    "avg_temperature": float(result.avg_temperature or 0),
                    "avg_vibration": float(result.avg_vibration or 0),
                    "avg_gas": float(result.avg_gas or 0),
                    "avg_power": float(result.avg_power or 0),
                }
            return None
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch stats: {str(e)}")
            return None
        finally:
            session.close()

    def get_for_ml_pipeline(
        self,
        device_id: Optional[str] = None,
        limit: int = 1000,
    ) -> dict:
        """
        Retrieve sensor data in numpy-ready format for ML pipeline.

        Returns a dictionary containing arrays of sensor values, prepared for
        normalization and feature engineering. This is a placeholder for future
        ML integration.

        Args:
            device_id: Optional device ID to filter by specific device
            limit: Maximum number of records to retrieve

        Returns:
            Dictionary with keys:
                - timestamps: List of ISO format timestamps
                - temperatures: List of float values
                - vibrations: List of float values
                - gases: List of float values
                - powers: List of float values
                - device_ids: List of device identifiers
                - raw_data: Original SensorReading objects (for reference)
        """
        readings = self.get_history(device_id=device_id, limit=limit)

        if not readings:
            logger.warning(f"No data available for ML pipeline (device={device_id})")
            return {
                "timestamps": [],
                "temperatures": [],
                "vibrations": [],
                "gases": [],
                "powers": [],
                "device_ids": [],
                "raw_data": [],
            }

        return {
            "timestamps": [r.timestamp.isoformat() for r in readings],
            "temperatures": [r.temperature for r in readings],
            "vibrations": [r.vibration for r in readings],
            "gases": [r.gas for r in readings],
            "powers": [r.power for r in readings],
            "device_ids": [r.device_id for r in readings],
            "raw_data": readings,
        }

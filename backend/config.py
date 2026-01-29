"""
Configuration management for Machine-Guard backend.
Loads environment variables and provides validated configuration.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # MQTT Configuration
    mqtt_broker: str
    mqtt_port: int
    sensor_topic: str
    control_topic: str

    # Database Configuration (Firebase)
    use_firebase: bool
    firebase_credentials_path: Optional[str]
    firebase_database_url: Optional[str]
    
    # Legacy SQLite (optional fallback)
    database_url: str

    # Flask Configuration
    flask_host: str
    flask_port: int
    flask_debug: bool
    flask_env: str

    # Logging Configuration
    log_level: str

    @staticmethod
    def from_env() -> "Config":
        """
        Load configuration from environment variables with defaults.

        Returns:
            Config instance with validated values

        Raises:
            ValueError: If required environment variables are missing
        """
        # Load .env file if it exists
        env_path = Path(__file__).parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        mqtt_broker = os.getenv("MQTT_BROKER")
        if not mqtt_broker:
            raise ValueError("MQTT_BROKER environment variable is required")

        try:
            mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        except ValueError:
            raise ValueError("MQTT_PORT must be a valid integer")

        sensor_topic = os.getenv("SENSOR_TOPIC", "sensors/+/data")
        control_topic = os.getenv("CONTROL_TOPIC", "control/+/command")

        # Firebase Configuration
        use_firebase = os.getenv("USE_FIREBASE", "true").lower() == "true"
        firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        firebase_database_url = os.getenv("FIREBASE_DATABASE_URL")

        # SQLite fallback (legacy)
        database_url = os.getenv("DATABASE_URL", "sqlite:///sensor_data.db")

        flask_host = os.getenv("FLASK_HOST", "0.0.0.0")
        try:
            flask_port = int(os.getenv("FLASK_PORT", "5000"))
        except ValueError:
            raise ValueError("FLASK_PORT must be a valid integer")

        flask_debug = os.getenv("FLASK_ENV", "production") == "development"
        flask_env = os.getenv("FLASK_ENV", "production")
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        return Config(
            mqtt_broker=mqtt_broker,
            mqtt_port=mqtt_port,
            sensor_topic=sensor_topic,
            control_topic=control_topic,
            use_firebase=use_firebase,
            firebase_credentials_path=firebase_credentials_path,
            firebase_database_url=firebase_database_url,
            database_url=database_url,
            flask_host=flask_host,
            flask_port=flask_port,
            flask_debug=flask_debug,
            flask_env=flask_env,
            log_level=log_level,
        )


def get_config() -> Config:
    """
    Get the application configuration.

    Returns:
        Configured Config instance
    """
    return Config.from_env()


import sys
import threading
from typing import Optional

from flask import Flask
from flask_cors import CORS

from config import get_config
from firebase_config import FirebaseDB
from database import Database
from mqtt_client import MQTTClient
from routes.sensors import sensors_bp, set_database as set_sensors_db
from routes.system import system_bp
from routes.control import control_bp
from utils.logger import setup_logger

# Initialize logger
logger = setup_logger(__name__)

# Global references
app: Optional[Flask] = None
db: Optional[Database] = None
mqtt_client: Optional[MQTTClient] = None


def create_app() -> Flask:
    """
    Create and configure Flask application.

    Returns:
        Configured Flask app instance
    """
    global app, db, mqtt_client

    try:
        logger.info("=" * 60)
        logger.info("Initializing Machine-Guard IoT Backend")
        logger.info("=" * 60)

        # Load configuration
        config = get_config()
        
        # Initialize database (Firebase or SQLite)
        if config.use_firebase:
            logger.info("Using Firebase Realtime Database")
            db = FirebaseDB(
                config.firebase_credentials_path,
                config.firebase_database_url
            )
            logger.info(f"Firebase Database: {config.firebase_database_url}")
        else:
            logger.info("Using SQLite Database (legacy)")
            db = Database(config.database_url)
            logger.info(f"Database={config.database_url}")

        # Initialize Flask app
        app = Flask(__name__)
        app.config["JSON_SORT_KEYS"] = False

        # Enable CORS for all routes
        CORS(app, resources={r"/api/*": {"origins": "*"}})
        logger.info("CORS enabled for all routes")

        # Database already initialized above
        logger.info("Database initialized successfully")

        # Set database for sensor routes
        set_sensors_db(db)

        # Register blueprints (routes)
        app.register_blueprint(sensors_bp)
        app.register_blueprint(system_bp)
        app.register_blueprint(control_bp)
        logger.info("API blueprints registered")

        # Initialize MQTT client
        def on_sensor_data(data: dict) -> None:
            """Callback function to handle validated sensor data from MQTT."""
            logger.debug(f"Processing sensor data: {data}")
            result = db.insert_reading(data)
            if result:
                logger.info(
                    f"Sensor data stored: device={data['device_id']}, "
                    f"temp={data['temperature']:.2f}°C"
                )

        try:
            mqtt_client = MQTTClient(
                broker=config.mqtt_broker,
                port=config.mqtt_port,
                sensor_topic=config.sensor_topic,
                control_topic=config.control_topic,
                on_message_callback=on_sensor_data,
            )
            mqtt_client.connect()
            logger.info("MQTT client connected")
        except Exception as e:
            logger.error(f"Failed to initialize MQTT client: {str(e)}")
            # Don't exit - API can still function without MQTT
            logger.warning("Continuing without MQTT. Sensor data ingestion will not work.")

        logger.info("=" * 60)
        logger.info("Machine-Guard Backend initialized successfully!")
        logger.info("=" * 60)

        return app

    except Exception as e:
        logger.critical(f"Failed to initialize application: {str(e)}")
        raise


def shutdown_gracefully() -> None:
    """Gracefully shutdown MQTT client and close database connections."""
    logger.info("Shutting down Machine-Guard Backend...")

    if mqtt_client:
        try:
            mqtt_client.disconnect()
            logger.info("MQTT client disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting MQTT client: {str(e)}")

    logger.info("Shutdown complete")


def main() -> None:
    """Main entry point for the application."""
    try:
        config = get_config()
        app = create_app()

        # Register shutdown handler
        import atexit
        atexit.register(shutdown_gracefully)

        # Run Flask development server
        logger.info(
            f"Starting Flask server on {config.flask_host}:{config.flask_port}"
        )
        app.run(
            host=config.flask_host,
            port=config.flask_port,
            debug=config.flask_debug,
            use_reloader=False,  # Disable reloader to prevent MQTT client duplication
        )

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        shutdown_gracefully()
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Application error: {str(e)}")
        shutdown_gracefully()
        sys.exit(1)


if __name__ == "__main__":
    main()

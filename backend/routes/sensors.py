"""
Sensor data endpoints for Machine-Guard backend.
Exposes REST APIs for querying sensor readings and device information.
"""

from flask import Blueprint, jsonify, request
from typing import Tuple

from database import Database
from utils.logger import setup_logger

logger = setup_logger(__name__)

sensors_bp = Blueprint("sensors", __name__, url_prefix="/api/sensors")

# Global database instance (will be set by app.py)
db: Database = None


def set_database(database: Database) -> None:
    """
    Set the global database instance for this module.

    Args:
        database: Initialized Database instance
    """
    global db
    db = database


@sensors_bp.route("/latest", methods=["GET"])
def get_latest_sensor_data() -> Tuple[dict, int]:
    """
    Get the latest sensor reading from all devices or a specific device.

    Query Parameters:
        device_id (optional): Filter by specific device ID

    Returns:
        JSON response with latest sensor reading or error message
    """
    if db is None:
        logger.error("Database not initialized")
        return jsonify({"error": "Database not initialized"}), 500

    try:
        device_id = request.args.get("device_id")
        reading = db.get_latest_reading(device_id=device_id)

        if reading is None:
            return jsonify({
                "message": "No sensor readings found",
                "device_id": device_id,
            }), 404

        return jsonify({
            "data": reading.to_dict(),
        }), 200

    except Exception as e:
        logger.error(f"Error fetching latest reading: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@sensors_bp.route("/history", methods=["GET"])
def get_sensor_history() -> Tuple[dict, int]:
    """
    Get historical sensor readings with pagination.

    Query Parameters:
        device_id (optional): Filter by specific device ID
        limit (optional): Maximum records to return (default: 100, max: 10000)
        offset (optional): Number of records to skip (default: 0)

    Returns:
        JSON response with list of sensor readings
    """
    if db is None:
        logger.error("Database not initialized")
        return jsonify({"error": "Database not initialized"}), 500

    try:
        device_id = request.args.get("device_id")
        
        # Parse and validate limit
        limit_str = request.args.get("limit", "100")
        try:
            limit = int(limit_str)
            limit = min(max(limit, 1), 10000)  # Clamp between 1 and 10000
        except ValueError:
            return jsonify({"error": "Invalid limit parameter"}), 400

        # Parse and validate offset
        offset_str = request.args.get("offset", "0")
        try:
            offset = int(offset_str)
            offset = max(offset, 0)
        except ValueError:
            return jsonify({"error": "Invalid offset parameter"}), 400

        readings = db.get_history(device_id=device_id, limit=limit, offset=offset)

        return jsonify({
            "count": len(readings),
            "limit": limit,
            "offset": offset,
            "device_id": device_id,
            "data": [reading.to_dict() for reading in readings],
        }), 200

    except Exception as e:
        logger.error(f"Error fetching sensor history: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@sensors_bp.route("/stats", methods=["GET"])
def get_sensor_stats() -> Tuple[dict, int]:
    """
    Get aggregated statistics for sensor readings.

    Query Parameters:
        device_id (optional): Filter by specific device ID

    Returns:
        JSON response with aggregated statistics
    """
    if db is None:
        logger.error("Database not initialized")
        return jsonify({"error": "Database not initialized"}), 500

    try:
        device_id = request.args.get("device_id")
        stats = db.get_stats(device_id=device_id)

        if stats is None:
            return jsonify({
                "message": "No statistics available",
                "device_id": device_id,
            }), 404

        return jsonify({
            "stats": stats,
            "device_id": device_id,
        }), 200

    except Exception as e:
        logger.error(f"Error fetching statistics: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@sensors_bp.route("/ml-data", methods=["GET"])
def get_ml_pipeline_data() -> Tuple[dict, int]:
    """
    Get sensor data in numpy-ready format for ML pipeline.

    Query Parameters:
        device_id (optional): Filter by specific device ID
        limit (optional): Maximum records to retrieve (default: 1000)

    Returns:
        JSON response with structured data for ML processing
    """
    if db is None:
        logger.error("Database not initialized")
        return jsonify({"error": "Database not initialized"}), 500

    try:
        device_id = request.args.get("device_id")
        
        # Parse and validate limit
        limit_str = request.args.get("limit", "1000")
        try:
            limit = int(limit_str)
            limit = min(max(limit, 1), 100000)  # Clamp between 1 and 100000
        except ValueError:
            return jsonify({"error": "Invalid limit parameter"}), 400

        ml_data = db.get_for_ml_pipeline(device_id=device_id, limit=limit)

        return jsonify({
            "sample_count": len(ml_data["temperatures"]),
            "device_id": device_id,
            "data": {
                "timestamps": ml_data["timestamps"],
                "temperatures": ml_data["temperatures"],
                "vibrations": ml_data["vibrations"],
                "gases": ml_data["gases"],
                "powers": ml_data["powers"],
                "device_ids": ml_data["device_ids"],
            },
        }), 200

    except Exception as e:
        logger.error(f"Error fetching ML data: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

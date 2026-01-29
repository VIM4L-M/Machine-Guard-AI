"""
Control command endpoint for Machine-Guard backend.
Handles incoming control/command messages from the frontend.
"""

from flask import Blueprint, jsonify, request
from typing import Tuple

from utils.logger import setup_logger

logger = setup_logger(__name__)

control_bp = Blueprint("control", __name__, url_prefix="/api")


@control_bp.route("/control", methods=["POST"])
def send_control_command() -> Tuple[dict, int]:
    """
    Send a control command to IoT devices via MQTT.

    Expected JSON body:
    {
        "device_id": "device_identifier",
        "command": "command_name",
        "parameters": {...}
    }

    Returns:
        JSON response with command acknowledgment or error
    """
    try:
        payload = request.get_json()

        if not payload:
            return jsonify({"error": "No JSON payload provided"}), 400

        # Validate required fields
        device_id = payload.get("device_id")
        command = payload.get("command")

        if not device_id or not command:
            return jsonify({
                "error": "Missing required fields: device_id, command"
            }), 400

        logger.info(f"Received control command: device={device_id}, command={command}")

        # TODO: Implement MQTT publishing for control commands
        # This is a placeholder for future implementation

        return jsonify({
            "status": "acknowledged",
            "device_id": device_id,
            "command": command,
            "message": "Command will be sent to device (implementation pending)",
        }), 202

    except Exception as e:
        logger.error(f"Error processing control command: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

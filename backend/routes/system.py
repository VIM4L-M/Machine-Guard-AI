"""
System and health check endpoints for Machine-Guard backend.
"""

from flask import Blueprint, jsonify

from utils.logger import setup_logger

logger = setup_logger(__name__)

system_bp = Blueprint("system", __name__, url_prefix="/api")


@system_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for the API.

    Returns:
        JSON response with status information
    """
    return jsonify({
        "status": "healthy",
        "service": "Machine-Guard IoT Backend",
        "version": "1.0.0",
    }), 200

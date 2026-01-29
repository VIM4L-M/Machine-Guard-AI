"""
Machine-Guard ML Backend
Real-time anomaly detection and failure prediction for IoT sensors.
"""

__version__ = "1.0.0"
__author__ = "Machine-Guard Team"

from ml_backend.mqtt_client import MLMQTTClient
from ml_backend.anomaly_detector import AnomalyDetector

__all__ = ["MLMQTTClient", "AnomalyDetector"]

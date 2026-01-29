"""
Main ML Backend Application
Integrates MQTT client with anomaly detection for real-time predictions.
"""

import json
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

from mqtt_client import MLMQTTClient
from anomaly_detector import AnomalyDetector

# Load environment variables
load_dotenv()


class MLBackend:
    """
    Main ML Backend that processes real-time sensor data from MQTT.
    """

    def __init__(self):
        """Initialize ML backend."""
        self.detector = AnomalyDetector()
        self.mqtt_client = None
        self.predictions_log = []
        self.max_log_size = 1000

    def setup_mqtt(self):
        """Setup MQTT client with callback."""
        self.mqtt_client = MLMQTTClient(
            broker=os.getenv("MQTT_BROKER", "broker.hivemq.com"),
            port=int(os.getenv("MQTT_PORT", 1883)),
            sensor_topic=os.getenv("MQTT_TOPIC", "iot/esp32/test"),
            on_data_callback=self.process_sensor_data,
        )

    def process_sensor_data(self, sensor_data: dict) -> None:
        """
        Process incoming sensor data and generate predictions.

        Args:
            sensor_data: Dictionary with sensor values from MQTT
        """
        try:
            # Generate health report
            report = self.detector.get_health_report(sensor_data)

            # Log the results
            self.predictions_log.append(report)
            if len(self.predictions_log) > self.max_log_size:
                self.predictions_log.pop(0)

            # Display results
            self._display_report(report)

            # Check if alerts need to be sent
            self._check_alerts(report)

        except Exception as e:
            print(f"❌ Error processing sensor data: {str(e)}")

    def _display_report(self, report: dict) -> None:
        """
        Display the health report in a formatted way.

        Args:
            report: Health report dictionary
        """
        # Get the health color based on score
        score = report["health_score"]
        if score >= 80:
            color = "✓"
            status = "GOOD"
        elif score >= 60:
            color = "⚠️"
            status = "FAIR"
        elif score >= 40:
            color = "⚠️"
            status = "POOR"
        else:
            color = "⛔"
            status = "CRITICAL"

        # Print formatted report
        print(f"\n{'='*70}")
        print(f"{color} HEALTH REPORT - {report['timestamp']}")
        print(f"{'='*70}")
        print(f"Health Score: {score}/100 ({status})")
        print(f"Recommendation: {report['recommendation']}")

        # Print sensor data
        print(f"\nSensor Data:")
        for sensor, value in report["sensor_data"].items():
            print(f"  {sensor:15} = {value}")

        # Print anomalies if any
        if report["anomalies"]["anomalies"]:
            print(f"\n⚠️  ANOMALIES DETECTED:")
            for anomaly in report["anomalies"]["anomalies"]:
                print(f"  - {anomaly['sensor']}: {anomaly['value']} ({anomaly['reason']})")

        # Print warnings if any
        if report["anomalies"]["warnings"]:
            print(f"\nℹ️  WARNINGS:")
            for warning in report["anomalies"]["warnings"]:
                print(f"  - {warning['sensor']}: z-score = {warning['z_score']:.2f}")

        # Print failure predictions if any
        if report["failure_predictions"]["predictions"]:
            print(f"\n⛔ FAILURE PREDICTIONS:")
            for pred in report["failure_predictions"]["predictions"]:
                print(f"  - {pred['issue']} ({pred['risk_level']})")
                print(f"    Recommendation: {pred['recommendation']}")

    def _check_alerts(self, report: dict) -> None:
        """
        Check if alerts need to be sent based on report.

        Args:
            report: Health report dictionary
        """
        # You can integrate email, SMS, or other alerting systems here
        if report["failure_predictions"]["overall_risk"] == "critical":
            print(f"\n🚨 CRITICAL ALERT TRIGGERED!")
            # TODO: Send email/SMS/Slack notification
            pass

        if report["health_score"] < 40:
            print(f"\n🚨 LOW HEALTH SCORE ALERT!")
            # TODO: Send email/SMS/Slack notification
            pass

    def get_statistics(self) -> dict:
        """
        Get statistics about the detector and predictions.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_readings_processed": len(self.predictions_log),
            "recent_readings": len(self.mqtt_client.data_buffer) if self.mqtt_client else 0,
            "detector_history_size": {k: len(v) for k, v in self.detector.history.items()},
            "last_report_timestamp": self.predictions_log[-1]["timestamp"] if self.predictions_log else None,
        }

    def start(self) -> None:
        """Start the ML backend."""
        print("\n" + "="*70)
        print("🤖 Machine-Guard ML Backend Starting...")
        print("="*70)

        try:
            # Setup MQTT connection
            self.setup_mqtt()
            self.mqtt_client.connect()

            # Keep running
            print("\n✓ ML Backend is running. Press Ctrl+C to stop.\n")
            import time
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down ML Backend...")
            if self.mqtt_client:
                self.mqtt_client.disconnect()
            print("✓ ML Backend stopped")

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            raise


if __name__ == "__main__":
    backend = MLBackend()
    backend.start()

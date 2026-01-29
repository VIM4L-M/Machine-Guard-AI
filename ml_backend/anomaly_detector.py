"""
ML Model for anomaly detection on sensor data.
Detects abnormal readings from IoT sensors in real-time.
"""

import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional


class AnomalyDetector:
    """
    Detects anomalies in sensor readings using statistical methods.
    """

    def __init__(self):
        """Initialize the anomaly detector."""
        # Normal ranges for different sensors (can be tuned)
        self.sensor_ranges = {
            "temperature": {"min": 15, "max": 40},  # °C
            "humidity": {"min": 20, "max": 80},      # %
            "gas": {"min": 300, "max": 1500},        # ppm equivalent
            "vibration": {"min": 0, "max": 100},     # Arbitrary units
            "power": {"min": 0, "max": 10},          # Watts
        }

        # Store historical data for statistical analysis
        self.history = {
            "temperature": [],
            "humidity": [],
            "gas": [],
            "vibration": [],
            "power": [],
        }
        self.max_history = 100  # Keep last 100 readings

    def update_history(self, sensor_data: Dict) -> None:
        """
        Update historical data with new sensor reading.

        Args:
            sensor_data: Dictionary with sensor values
        """
        for key in self.history.keys():
            if key in sensor_data:
                value = float(sensor_data[key])
                self.history[key].append(value)
                # Keep only last N readings
                if len(self.history[key]) > self.max_history:
                    self.history[key].pop(0)

    def get_statistics(self, sensor_type: str) -> Dict:
        """
        Get statistical information for a sensor type.

        Args:
            sensor_type: Type of sensor (e.g., 'temperature')

        Returns:
            Dictionary with mean, std, min, max
        """
        data = self.history.get(sensor_type, [])
        if not data:
            return {}

        return {
            "mean": np.mean(data),
            "std": np.std(data),
            "min": np.min(data),
            "max": np.max(data),
            "count": len(data),
        }

    def detect_anomalies(self, sensor_data: Dict) -> Dict:
        """
        Detect anomalies in sensor readings.

        Args:
            sensor_data: Dictionary with sensor values

        Returns:
            Dictionary with anomaly results
        """
        anomalies = []
        warnings = []

        for sensor_type, value in sensor_data.items():
            if sensor_type not in self.sensor_ranges:
                continue

            value = float(value)
            ranges = self.sensor_ranges[sensor_type]

            # Rule 1: Check if value is outside normal range
            if value < ranges["min"] or value > ranges["max"]:
                anomalies.append({
                    "sensor": sensor_type,
                    "value": value,
                    "reason": f"Outside range [{ranges['min']}, {ranges['max']}]",
                    "severity": "high",
                })

            # Rule 2: Check if value deviates from mean by 2+ standard deviations
            stats = self.get_statistics(sensor_type)
            if stats and "std" in stats and stats["std"] > 0:
                z_score = abs((value - stats["mean"]) / stats["std"])
                if z_score > 2:  # 2-sigma rule
                    warnings.append({
                        "sensor": sensor_type,
                        "value": value,
                        "mean": stats["mean"],
                        "std": stats["std"],
                        "z_score": z_score,
                        "reason": f"Deviation from mean ({z_score:.2f} sigma)",
                        "severity": "medium",
                    })

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "anomalies": anomalies,
            "warnings": warnings,
            "is_normal": len(anomalies) == 0,
        }

    def predict_failure(self, sensor_data: Dict) -> Dict:
        """
        Predict potential equipment failure based on sensor readings.

        Args:
            sensor_data: Dictionary with sensor values

        Returns:
            Dictionary with failure predictions
        """
        predictions = []

        # Rule 1: High vibration + high temperature = potential bearing failure
        vibration = float(sensor_data.get("vibration", 0))
        temperature = float(sensor_data.get("temperature", 0))

        if vibration > 60 and temperature > 35:
            predictions.append({
                "issue": "Possible bearing failure",
                "risk_level": "high",
                "indicators": ["High vibration", "High temperature"],
                "recommendation": "Inspect bearings immediately",
            })

        # Rule 2: High gas levels = potential combustible hazard
        gas = float(sensor_data.get("gas", 0))
        if gas > 1200:
            predictions.append({
                "issue": "High gas concentration detected",
                "risk_level": "critical",
                "indicators": ["Gas level > 1200 ppm"],
                "recommendation": "Activate ventilation system",
            })

        # Rule 3: Low power consumption = potential sensor/device failure
        power = float(sensor_data.get("power", 0))
        if power < 0.1:
            predictions.append({
                "issue": "Low power reading",
                "risk_level": "medium",
                "indicators": ["Power < 0.1W"],
                "recommendation": "Check sensor connections",
            })

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "predictions": predictions,
            "overall_risk": "critical" if predictions else "normal",
        }

    def get_health_report(self, sensor_data: Dict) -> Dict:
        """
        Generate comprehensive health report for the equipment.

        Args:
            sensor_data: Dictionary with sensor values

        Returns:
            Dictionary with comprehensive health analysis
        """
        self.update_history(sensor_data)

        anomaly_result = self.detect_anomalies(sensor_data)
        failure_result = self.predict_failure(sensor_data)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "sensor_data": sensor_data,
            "anomalies": anomaly_result,
            "failure_predictions": failure_result,
            "health_score": self._calculate_health_score(anomaly_result, failure_result),
            "recommendation": self._get_recommendation(anomaly_result, failure_result),
        }

    def _calculate_health_score(self, anomaly_result: Dict, failure_result: Dict) -> int:
        """
        Calculate overall health score (0-100).

        Args:
            anomaly_result: Anomaly detection results
            failure_result: Failure prediction results

        Returns:
            Health score from 0 (critical) to 100 (excellent)
        """
        score = 100

        # Deduct points for anomalies
        score -= len(anomaly_result["anomalies"]) * 20

        # Deduct points for failure predictions
        if failure_result["predictions"]:
            for pred in failure_result["predictions"]:
                if pred["risk_level"] == "critical":
                    score -= 30
                elif pred["risk_level"] == "high":
                    score -= 15
                else:
                    score -= 5

        return max(0, min(100, score))

    def _get_recommendation(self, anomaly_result: Dict, failure_result: Dict) -> str:
        """
        Get maintenance recommendation based on results.

        Args:
            anomaly_result: Anomaly detection results
            failure_result: Failure prediction results

        Returns:
            String with recommendation
        """
        if failure_result["overall_risk"] == "critical":
            return "⛔ CRITICAL: Immediate action required"
        elif len(anomaly_result["anomalies"]) > 0:
            return "⚠️  WARNING: Anomalies detected, schedule maintenance"
        elif len(anomaly_result["warnings"]) > 0:
            return "ℹ️  INFO: Monitor closely, no action needed now"
        else:
            return "✓ NORMAL: Equipment operating normally"


if __name__ == "__main__":
    # Example usage
    detector = AnomalyDetector()

    # Simulate sensor readings
    test_data = [
        {"temperature": 25.0, "humidity": 45.0, "gas": 800, "vibration": 20, "power": 2.5},
        {"temperature": 26.5, "humidity": 48.0, "gas": 850, "vibration": 22, "power": 2.7},
        {"temperature": 28.0, "humidity": 50.0, "gas": 900, "vibration": 25, "power": 3.0},
        {"temperature": 35.0, "humidity": 65.0, "gas": 1200, "vibration": 70, "power": 4.5},  # Anomaly
    ]

    for data in test_data:
        report = detector.get_health_report(data)
        print(f"\n{'='*60}")
        print(f"Health Report: {report['timestamp']}")
        print(f"{'='*60}")
        print(f"Sensor Data: {report['sensor_data']}")
        print(f"Health Score: {report['health_score']}/100")
        print(f"Recommendation: {report['recommendation']}")

        if report["anomalies"]["anomalies"]:
            print(f"\nAnomalies Detected:")
            for anomaly in report["anomalies"]["anomalies"]:
                print(f"  - {anomaly['sensor']}: {anomaly['reason']}")

        if report["failure_predictions"]["predictions"]:
            print(f"\nPredictions:")
            for pred in report["failure_predictions"]["predictions"]:
                print(f"  - {pred['issue']} ({pred['risk_level']})")

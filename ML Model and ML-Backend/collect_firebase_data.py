
import requests
import csv
import time
import os
import sys

# Configuration
# Note: Using the same endpoint as the monitor script for consistency
FIREBASE_URL = "https://machine-guard-21f0a-default-rtdb.firebaseio.com/sensor_readings/esp32.json"
POLL_INTERVAL = 2.0
# The columns must match training_data.csv
CSV_HEADER = ["temperature", "humidity", "gas", "vibration", "current"]

def fetch_data():
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error fetching data: {e}")
    return None

def main():
    print(f"Starting data collection from {FIREBASE_URL}...")
    print(f"Format: {','.join(CSV_HEADER)}")
    
    try:
        while True:
            data = fetch_data()
            
            if data:
                # Extract device_id for filename
                # If 'device_id' is missing from the payload, default to 'esp32' (since we are querying the esp32 node directly)
                device_id = data.get("device_id", "esp32")
                filename = f"{device_id}.csv"
                
                # Map fields
                try:
                    # MAPPING: power -> current
                    # Using get() to handle missing keys safely (though we filter later)
                    row = {
                        "temperature": data.get("temperature"),
                        "humidity": data.get("humidity"),
                        "gas": data.get("gas"),
                        "vibration": data.get("vibration"),
                        "current": data.get("power") # Map power to current
                    }
                    
                    # Check for incomplete data
                    # If any required field is None, skip writing
                    if any(v is None for v in row.values()):
                        print(f"Skipping incomplete data packet: {row}")
                    else:
                        file_exists = os.path.isfile(filename)
                        
                        with open(filename, mode='a', newline='') as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADER)
                            
                            if not file_exists:
                                writer.writeheader()
                                print(f"Created new file: {filename}")
                            
                            writer.writerow(row)
                            
                            # Print confirmation (single line log)
                            values_str = ", ".join([f"{k}={v}" for k, v in row.items()])
                            print(f"Logged to {filename}: {values_str}")
                            
                except Exception as e:
                    print(f"Error processing data fields: {e}")
            
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        print("\nData collection stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()

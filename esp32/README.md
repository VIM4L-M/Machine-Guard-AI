# ESP32 Setup Guide for Machine-Guard

## ⚠️ Security Setup (Important!)

**Before uploading code, configure your credentials securely:**

### 1. Copy the example environment file:
```bash
cp .env.example .env
```

### 2. Edit `.env` with your WiFi credentials:
```
WIFI_SSID=your_wifi_network_name
WIFI_PASSWORD=your_wifi_password
MQTT_SERVER=broker.hivemq.com
MQTT_PORT=1883
```

### 3. Create `credentials.h` file:
```cpp
#ifndef CREDENTIALS_H
#define CREDENTIALS_H

const char* ssid = "your_wifi_ssid";
const char* password = "your_wifi_password";
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

#endif
```

**📌 Note:** Both `.env` and `credentials.h` are in `.gitignore` to prevent accidentally committing sensitive data to GitHub.

---

## Hardware Requirements

1. **ESP32 Development Board** (ESP32-DevKitC or similar)
2. **Sensors** (optional for testing):
   - Temperature sensor (TMP36, DHT22, or DS18B20)
   - Vibration sensor (SW-420 or similar)
   - Gas sensor (MQ-135, MQ-2, or similar)
   - Current sensor (ACS712 or INA219)
3. **USB Cable** for programming
4. **Breadboard and jumper wires**

## Software Requirements

1. **Arduino IDE** (version 1.8.x or 2.x)
2. **ESP32 Board Support**
3. **Required Libraries**:
   - `WiFi` (built-in with ESP32)
   - `PubSubClient` (MQTT client)
   - `ArduinoJson` (JSON serialization)

## Step 1: Install Arduino IDE

```bash
# On Arch Linux
sudo pacman -S arduino

# Or download from: https://www.arduino.cc/en/software
```

## Step 2: Add ESP32 Board Support

1. Open Arduino IDE
2. Go to **File → Preferences**
3. Add this URL to "Additional Board Manager URLs":
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Go to **Tools → Board → Boards Manager**
5. Search for "esp32" and install "**esp32 by Espressif Systems**"

## Step 3: Install Required Libraries

1. Go to **Sketch → Include Library → Manage Libraries**
2. Install these libraries:
   - Search "**PubSubClient**" by Nick O'Leary → Install
   - Search "**ArduinoJson**" by Benoit Blanchon → Install (version 6.x)

## Step 4: Configure Credentials (IMPORTANT!)

**⚠️ Never commit WiFi passwords to GitHub!**

1. Create a `credentials.h` file in the `esp32` folder:
```cpp
#ifndef CREDENTIALS_H
#define CREDENTIALS_H

const char* ssid = "YourWiFiName";
const char* password = "YourWiFiPassword";
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

#endif
```

2. The `.ino` file will automatically include this file
3. `credentials.h` is already in `.gitignore` - it won't be pushed to GitHub

### Finding MQTT Broker Address

```bash
# On Linux
ip addr show | grep "inet " | grep -v 127.0.0.1

# Or simply
hostname -I
```

Use the IP that's on the same network as your WiFi (usually starts with `192.168.x.x` or `172.16.x.x`).

## Step 5: Upload to ESP32

1. Connect ESP32 to your computer via USB
2. In Arduino IDE:
   - **Tools → Board** → Select "ESP32 Dev Module"
   - **Tools → Port** → Select the USB port (usually `/dev/ttyUSB0` on Linux)
   - **Tools → Upload Speed** → 115200
3. Click **Upload** button (→)
4. Wait for "Done uploading" message

## Step 6: Monitor Serial Output

1. Open **Tools → Serial Monitor**
2. Set baud rate to **115200**
3. You should see:
   ```
   === AutoForge ESP32 Sensor Client ===
   Connecting to WiFi: YourWiFiName
   .....
   ✓ WiFi connected!
   IP address: 192.168.1.100
   Attempting MQTT connection... connected!
   Subscribed to: control/ESP32_001/command
   ✓ Published: {"device_id":"ESP32_001","temperature":25.3,...}
   ```

## Step 7: Verify Backend Reception

On your laptop, check if the backend is receiving data:

```bash
# Terminal 1: Backend should show MQTT messages
# (Watch the terminal where app.py is running)

# Terminal 2: Query the API
curl 'http://localhost:5000/api/sensors/latest'
curl 'http://localhost:5000/api/sensors/history?limit=10'
```

You should see sensor data from your ESP32!

## Troubleshooting

### WiFi Connection Failed
- Double-check SSID and password (case-sensitive)
- Ensure ESP32 is within WiFi range
- Try resetting ESP32 (press EN button)

### MQTT Connection Failed
- Verify Mosquitto is running: `ps aux | grep mosquitto`
- Check laptop's IP address: `hostname -I`
- Ensure firewall allows port 1883:
  ```bash
  sudo ufw allow 1883/tcp
  ```
- Test MQTT from laptop:
  ```bash
  mosquitto_sub -h localhost -t "sensors/data" -v
  ```

### No Data in Backend
- Check Serial Monitor for "✓ Published" messages
- Verify MQTT topic matches (default: `sensors/data`)
- Check `.env` file has correct `SENSOR_TOPIC=sensors/+/data`

### Compilation Errors
- Ensure ESP32 board support is installed
- Verify all libraries are installed (PubSubClient, ArduinoJson)
- Try updating Arduino IDE to latest version

## Hardware Wiring (Optional Sensors)

### Temperature Sensor (TMP36)
```
TMP36 Pin 1 (Vcc)  → ESP32 3.3V
TMP36 Pin 2 (Out)  → ESP32 GPIO34
TMP36 Pin 3 (GND)  → ESP32 GND
```

### Vibration Sensor (SW-420)
```
SW-420 VCC → ESP32 3.3V
SW-420 OUT → ESP32 GPIO35
SW-420 GND → ESP32 GND
```

### Gas Sensor (MQ-135)
```
MQ-135 VCC → ESP32 5V (if available) or 3.3V
MQ-135 A0  → ESP32 GPIO32
MQ-135 GND → ESP32 GND
```

## Next Steps

1. **Test with real sensors** - Connect actual sensors to the GPIO pins
2. **Calibrate readings** - Adjust conversion formulas in the code
3. **Add deep sleep** - For battery-powered deployments
4. **Implement OTA updates** - Update firmware over WiFi
5. **Add TLS/SSL** - Secure MQTT communication

## Testing Without Physical Sensors

The sketch works even without sensors! It reads analog pins and generates simulated data. You can:
- Upload the sketch as-is to test connectivity
- View data in the Serial Monitor
- Query the backend API to see the data

Once connectivity works, connect real sensors and adjust the conversion formulas in the code.

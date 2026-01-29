#include <DHT.h>
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <hd44780.h>
#include <hd44780ioClass/hd44780_I2Cexp.h>
#include "credentials.h"  // WiFi and MQTT credentials

/* ================= PIN DEFINITIONS ================= */
#define DHTPIN 4
#define DHTTYPE DHT11
#define MQ2_PIN 34
#define VIBRATION_PIN 27
#define CURRENT_PIN 35

unsigned long lastVibrationTime = 0;


/* ================= OBJECTS ================= */
DHT dht(DHTPIN, DHTTYPE);
hd44780_I2Cexp lcd;

WiFiClient espClient;
PubSubClient client(espClient);

/* ================= WIFI & MQTT ================= */
// WiFi and MQTT credentials are now in credentials.h
// This keeps sensitive information out of version control

/* ================= VARIABLES ================= */
unsigned long lastRead = 0;
const unsigned long interval = 2000;

int zeroCurrent = 0;

/* -------- vibration handling -------- */
volatile bool vibrationDetected = false; // 3 sec

/* ================= ISR ================= */
void IRAM_ATTR vibrationISR() {
  vibrationDetected = true;
  lastVibrationTime = millis();
}


/* ================= MQTT RECONNECT ================= */
void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    if (client.connect("ESP32_Vimal_Node")) {
      Serial.println(" connected");
    } else {
      Serial.print(" failed rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

/* ================= SETUP ================= */
void setup() {

  Serial.begin(9600);
  delay(1000);

  int status = lcd.begin(16, 2);
  if (status) {
    Serial.println("LCD init failed");
    while (1);
  }

  lcd.backlight();
  lcd.print("Connecting WiFi");

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  lcd.clear();
  lcd.print("WiFi Connected");

  Serial.println("\nWiFi connected");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  client.setServer(mqtt_server, mqtt_port);

  dht.begin();

  pinMode(VIBRATION_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(VIBRATION_PIN), vibrationISR, FALLING);

  lcd.clear();
  lcd.print("Calibrating...");
  delay(2000);

  long sum = 0;
  for (int i = 0; i < 500; i++) {
    sum += analogRead(CURRENT_PIN);
    delay(2);
  }
  zeroCurrent = sum / 500;

  lcd.clear();
  lcd.print("System Ready");
  delay(1500);
  lcd.clear();
}

/* ================= LOOP ================= */
void loop() {

  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  /* -------- ALERT MODE -------- */
  if (millis() - lastVibrationTime < 500) {

  lcd.setCursor(0, 0);
  lcd.print("!!! ALERT !!!   ");
  lcd.setCursor(0, 1);
  lcd.print("VIBRATION !!!   ");
  return;
}

  /* -------- NORMAL MODE -------- */
  if (millis() - lastRead >= interval) {
    lastRead = millis();

    float temp = dht.readTemperature();
    float hum  = dht.readHumidity();
    int gasVal = analogRead(MQ2_PIN);

    int currentRaw = analogRead(CURRENT_PIN);
    float current = (currentRaw - zeroCurrent) * 0.01;
    if (current < 0) current = 0;

    int vib = vibrationDetected ? 1 : 0;
    vibrationDetected = false;

    String payload = "{";
    payload += "\"temperature\":" + String(temp) + ",";
    payload += "\"humidity\":" + String(hum) + ",";
    payload += "\"gas\":" + String(gasVal) + ",";
    payload += "\"vibration\":" + String(vib) + ",";
    payload += "\"current\":" + String(current, 2);
    payload += "}";

    client.publish("iot/esp32/test", payload.c_str());
    Serial.println(payload);

    lcd.setCursor(0, 0);
    lcd.print("T:");
    lcd.print((int)temp);
    lcd.print(" I:");
    lcd.print(current, 1);
    lcd.print(" ");

    lcd.setCursor(0, 1);
    lcd.print("G:");
    lcd.print(gasVal);
    lcd.print(" H:");
    lcd.print((int)hum);
    lcd.print(" ");
  }
}
import network
import urequests
from machine import Pin, ADC
import time
import dht

# ------------------------------------
# THINGSPEAK SETTINGS
# ------------------------------------
THINGSPEAK_API_KEY = "RJV3BL9JSVJVG9JN"  

# ------------------------------------
# WIFI SETTINGS
# ------------------------------------
WIFI_SSID = "Swasthik"
WIFI_PASS = "12345671"

# ------------------------------------
# CONNECT TO WIFI
# ------------------------------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    print("Connecting to WiFi", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(0.5)
    print("\nWiFi Connected:", wlan.ifconfig())

connect_wifi()


# ------------------------------------
# SOIL MOISTURE SENSOR (ADC)
# ------------------------------------
soil = ADC(26)

def get_moisture():
    raw = soil.read_u16()
    percent = int((65535 - raw) * 100 / 65535)
    return percent


# ------------------------------------
# RELAY (PUMP CONTROL)
# ------------------------------------
pump = Pin(16, Pin.OUT)
pump.value(1)   # OFF initially


# ------------------------------------
# DHT22 SENSOR
# ------------------------------------
dht_sensor = dht.DHT22(Pin(17))


# ------------------------------------
# FAN RELAY
# ------------------------------------
fan = Pin(15, Pin.OUT)
fan.value(1)   # OFF initially


# ------------------------------------
# USER SETTINGS
# ------------------------------------
MOISTURE_THRESHOLD =0
TEMP_THRESHOLD =  30

print("Soil + DHT22 + Pump + Fan Monitoring Started...")
print("------------------------------------------------")


# ------------------------------------
# SEND DATA TO THINGSPEAK
# ------------------------------------
def send_to_thingspeak(temp, hum, moisture, fan_state, pump_state):
    try:
        url = (
            "https://api.thingspeak.com/update?api_key=" + THINGSPEAK_API_KEY +
            "&field1=" + str(temp) +
            "&field2=" + str(hum) +
            "&field3=" + str(moisture) +
            "&field4=" + str(fan_state) +
            "&field5=" + str(pump_state)
        )

        response = urequests.get(url)
        response.close()
        print("ThingSpeak Update OK")

    except Exception as e:
        print("ThingSpeak Error:", e)


# ------------------------------------
# MAIN LOOP
# ------------------------------------
while True:
    # Read Soil
    moisture = get_moisture()

    # Read DHT22
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()
    except Exception as e:
        print("DHT22 Error:", e)
        time.sleep(1)
        continue

    print("Soil:", moisture, "%  |  Temp:", temp, "°C  |  Hum:", hum, "%")

    # Pump Control
    if moisture < MOISTURE_THRESHOLD:
        print("Soil Dry → Pump ON")
        pump.value(1)     # Active-Low → ON
    else:
        print("Soil Wet → Pump OFF")
        pump.value(0)     # OFF

    # Fan Control
    if temp >= TEMP_THRESHOLD:
        print("High Temp → Fan ON")
        fan.value(1)      # Active-Low → ON
    else:
        print("Normal Temp → Fan OFF")
        fan.value(0)      # OFF

    # Convert relay states to 0/1 values
    fan_state = 1 if fan.value() == 1 else 0
    pump_state = 1 if pump.value() == 1 else 0

    # Send data to ThingSpeak
    send_to_thingspeak(temp, hum, moisture, fan_state, pump_state)

    print("-------------------------------------")
    time.sleep(20)   


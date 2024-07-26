"""script to continuously upload CPU and room temperature to local db"""
# pylint: disable=import-error, no-name-in-module
from datetime import datetime
import time
import os
import sys
import threading
import requests
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
# from ntfy import send_critical

sys.path.append(
    '/home/orangepi/Desktop/projects/orangepi/serial_communication/web/routes/communication'
)
# Load environment variables
DOTENV_PATH = '/home/orangepi/Desktop/projects/orangepi/serial_communication/web/.env'
load_dotenv(DOTENV_PATH)

# ThingSpeak API URLs
TEMPERATURE_URL = "https://api.thingspeak.com/channels/2201589/fields/1.json?results=1"
HUMIDITY_URL = "https://api.thingspeak.com/channels/2201589/fields/2.json?results=1"

# InfluxDB configuration
BUCKET = os.getenv("INFLUXDB_BUCKET")
ORGANIZATION = os.getenv("INFLUXDB_ORGANIZATION")
TOKEN = os.getenv("INFLUXDB_TOKEN")
INFLUX_URL = f"{os.getenv('LOCALHOST')}:{os.getenv('INFLUXDB_PORT')}"
MAX_TEMPERATURE = float(os.getenv("MAX_TEMPERATURE"))

# Initialize InfluxDB client
influx_client = InfluxDBClient(url=INFLUX_URL, token=TOKEN, org=ORGANIZATION)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# Store the last entry ID to check for new data
LAST_ENTRY_ID = None

def fetch_thingspeak_data(url):
    """Use to fetch data from the thingSpeak server."""
    response = requests.get(url, timeout=10)
    data = response.json()
    feeds = data["feeds"]
    return feeds[0] if feeds else None

def upload_to_influxdb(temperature, humidity):
    """Use to upload data to influx db server."""
    point = (
        Point("environment")
        .tag("source", "ThingSpeak")
        .field("temperature", temperature)
        .field("humidity", humidity)
        .time(datetime.utcnow(), WritePrecision.NS)
    )
    write_api.write(bucket=BUCKET, org=ORGANIZATION, record=point)
    print(f"Written to InfluxDB: temperature={temperature}, humidity={humidity}")

def manage_thingspeak():
    """Use to fetch data from thingSpeak."""
    global LAST_ENTRY_ID  # pylint: disable=global-statement
    while True:
        try:
            temp_data = fetch_thingspeak_data(TEMPERATURE_URL)
            humidity_data = fetch_thingspeak_data(HUMIDITY_URL)

            if temp_data and humidity_data:
                temp_entry_id = temp_data["entry_id"]
                humidity_entry_id = humidity_data["entry_id"]

                # Check if the latest data is new
                if (LAST_ENTRY_ID is None or
                    temp_entry_id > LAST_ENTRY_ID or
                    humidity_entry_id > LAST_ENTRY_ID):
                    temperature = float(temp_data["field1"])
                    humidity = float(humidity_data["field2"])

                    # Upload new data to InfluxDB
                    upload_to_influxdb(temperature, humidity)

                    # Update the last entry ID
                    LAST_ENTRY_ID = max(temp_entry_id, humidity_entry_id)
                else:
                    print("Skipping ThingSpeak as new value is not added")

            # Wait for 2 minutes before checking again
            time.sleep(120)
        except Exception as e: # pylint: disable=broad-except
            print("Unexpected error in function: manage_thingspeak", e)

def monitor_temperature():
    """Use to monitor CPU temperature."""
    while True:
        time.sleep(3)  # Wait for 3 seconds before the next reading
        try:
            temperatures = []

            # Loop through all thermal zones and fetch temperature values
            for zone in range(10):  # Assuming thermal zones are numbered from 0 to 9
                zone_path = f"/sys/class/thermal/thermal_zone{zone}"

                # Check if the thermal zone exists
                if os.path.exists(zone_path):
                    with open(os.path.join(zone_path, 'temp'), 'r', encoding='utf-8') as file:
                        # Convert temperature to an integer
                        temp = int(file.read().strip()) / 1000
                        temperatures.append(temp)

            if temperatures:
                # Calculate average and maximum temperature values
                average_temp = round(sum(temperatures) / len(temperatures), 2)
                max_temp = max(temperatures)

                # Create the point to write to InfluxDB
                point = (
                    Point("temperature")
                    .tag("source", "thermal_zones")
                    .field("average_temp", average_temp)
                    .field("max_temp", max_temp)
                )
                write_api.write(bucket=BUCKET, org=ORGANIZATION, record=point)
                print(f"Written to InfluxDB: avg_temp={average_temp}, max_temp={max_temp}")
                if max_temp > MAX_TEMPERATURE:
                    # send_critical(f"CPU temperature: {max_temp}")
                    print("Over heat alert!")
            else:
                print("No valid temperature values found.")

        except Exception as e: # pylint: disable=broad-except
            print("Unexpected error in function: monitor_temperature", e)

if __name__ == "__main__":
    # for stress testing:
    # sudo apt install stress
    # stress --cpu 8 --io 4 --vm 4 --vm-bytes 1024M --timeout 30s

    thread1 = threading.Thread(target=manage_thingspeak)
    thread2 = threading.Thread(target=monitor_temperature)

    thread1.start()
    thread2.start()

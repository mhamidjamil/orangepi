import requests
import time
from datetime import datetime
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
# from serial_communication.web.routes.communication.ntfy import send_critical
import threading

# ThingSpeak API URLs
temperature_url = "https://api.thingspeak.com/channels/2201589/fields/1.json?results=1"
humidity_url = "https://api.thingspeak.com/channels/2201589/fields/2.json?results=1"

DOTENV_PATH = '/home/orangepi/Desktop/projects/orangepi/serial_communication/web/.env'
load_dotenv(DOTENV_PATH)

BUCKET=os.getenv("INFLUXDB_BUCKET")
ORGANIZATION = os.getenv("INFLUXDB_ORGANIZATION")

token = os.getenv("INFLUXDB_TOKEN")
influx_url = os.getenv("LOCALHOST")+":"+os.getenv("INFLUXDB_PORT")
write_client = influxdb_client.InfluxDBClient(url=influx_url, token=token, org=ORGANIZATION)
MAX_TEMPERATURE=os.getenv("MAX_TEMPERATURE")

# Initialize InfluxDB client
write_client = InfluxDBClient(url=influx_url, token=token, org=ORGANIZATION)
write_api = write_client.write_api(write_options=SYNCHRONOUS)

# Store the last entry ID to check for new data
last_entry_id = None

def fetch_thingspeak_data(url):
    response = requests.get(url)
    data = response.json()
    feeds = data["feeds"]
    if feeds:
        return feeds[0]  # Return the latest entry
    return None

def upload_to_influxdb(temp, humidity):
    point = (
        Point("environment")
        .tag("source", "ThingSpeak")
        .field("temperature", temp)
        .field("humidity", humidity)
        .time(datetime.utcnow(), WritePrecision.NS)
    )
    write_api.write(bucket=BUCKET, org=ORGANIZATION, record=point)
    print(f"Written to InfluxDB: temperature={temp}, humidity={humidity}")

def manage_think_speak():
    while True:
        try:
            temp_data = fetch_thingspeak_data(temperature_url)
            humidity_data = fetch_thingspeak_data(humidity_url)

            if temp_data and humidity_data:
                temp_entry_id = temp_data["entry_id"]
                humidity_entry_id = humidity_data["entry_id"]

                global last_entry_id # pylint: disable=global-statement
                # Check if the latest data is new
                if last_entry_id is None or temp_entry_id > last_entry_id or humidity_entry_id > last_entry_id:
                    temperature = float(temp_data["field1"])
                    humidity = float(humidity_data["field2"])

                    # Upload new data to InfluxDB
                    upload_to_influxdb(temperature, humidity)

                    # Update the last entry ID
                    last_entry_id = max(temp_entry_id, humidity_entry_id)
                else:
                    print("skipping thingspeak as new value is not added")

            # Wait for 3 minutes before checking again
            time.sleep(120)
        except Exception as e: # pylint: disable=broad-except
            # exception_logger("Unexpected error in manage_think_speak", e)
            print("Unexpected error in function: manage_think_speak", e)

def monitor_temperature():
    while True:
        try:
            temperatures = []

            # Loop through all thermal zones and fetch temperature values
            for zone in range(0, 10):  # Assuming thermal zones are numbered from 0 to 9
                zone_path = f"/sys/class/thermal/thermal_zone{zone}"

                # Check if the thermal zone exists
                if os.path.exists(zone_path):
                    with open(os.path.join(zone_path, 'temp'), 'r') as file:
                        # Convert temperature to an integer
                        temp = int(file.read().strip())
                        temperatures.append(temp)

            if temperatures:
                write_api = write_client.write_api(write_options=SYNCHRONOUS)
                # Calculate average and maximum temperature values
                average_temp = sum(temperatures) / len(temperatures) / 1000
                max_temp = max(temperatures) / 1000

                # Create the point to write to InfluxDB
                point = (
                    Point("temperature")
                    .tag("source", "thermal_zones")
                    .field("average_temp", average_temp)
                    .field("max_temp", max_temp)
                )
                write_api.write(bucket=BUCKET, org=ORGANIZATION, record=point)
                print(f"Written to InfluxDB: avg_temp={average_temp}, max_temp={max_temp}")
                if int(max_temp) > int(MAX_TEMPERATURE):
                    # send_critical(f"CPU temperature: {max_temp}")
                    print("Over heat alert!")
            else:
                print("No valid temperature values found.")

            time.sleep(3)  # Wait for 3 seconds before the next reading
        except Exception as e: # pylint: disable=broad-except
            # exception_logger("monitor_temperature", e)
            print("unexpected error in function: monitor_temperature")

if __name__ == "__main__":
    thread = threading.Thread(target=manage_think_speak)
    thread2 = threading.Thread(target=monitor_temperature)

    thread.start()
    thread2.start()
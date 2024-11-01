"""This scrip will communicate with ttgo tcall"""

import threading
import time
import os
import random
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
DOTENV_PATH = '/home/orangepi/Desktop/projects/orangepi/serial_communication/web/.env'
load_dotenv(DOTENV_PATH)

# ESP32's IP address and endpoint
esp32_url = os.getenv("TTGO_TCALL_SERVER")

# Endpoint to handle POST requests from ESP32
@app.route('/esp32', methods=['POST'])
def handle_post():
    """This function will handle POST requests from ESP32"""
    if request.is_json:
        data = request.get_json()
        print(f"Received data from ESP32: {data['data']}")

        # Send a response back to ESP32
        response = {"response": "Data received successfully"}
        return jsonify(response), 200
    return jsonify({"error": "Request must be JSON"}), 400

# Function to send random data to ESP32 every 5 seconds
def send_data_to_esp32_periodically():
    """This function will send random data to ESP32 every 5 seconds"""
    while True:
        # Generate random data
        random_data = str(random.randint(1000, 9999))
        data_to_send = {"data": f"Random data: {random_data}"}

        try:
            # Send the data to ESP32 using a POST request
            response = requests.post(esp32_url, json=data_to_send, timeout=10)
            if response.status_code == 200:
                print(f"Sent data to ESP32: {data_to_send}")
            else:
                print(f"Failed to send data to ESP32. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending data to ESP32: {e}")

        time.sleep(5)

# Run the Flask app
if __name__ == '__main__':
    # Start the background thread to send data to ESP32 periodically
    threading.Thread(target=send_data_to_esp32_periodically, daemon=True).start()

    print (f"ESP32 url: {esp32_url}")

    # Start the Flask server
    app.run(host='0.0.0.0', port=6678)

#version: 1.0.1
#Version notes: app.py will now start communicating with module
from flask import Flask, render_template, request
import serial
import requests
import datetime
import schedule
import time
import os

app = Flask(__name__)
# Replace with your actual serial port
ser = serial.Serial('/dev/ttyACM0', 115200)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/read_serial')
def read_serial():
    data = ser.readline().decode('utf-8')
    return {'data': data}


@app.route('/send_serial', methods=['POST'])
def send_serial():
    data_to_send = request.form['data']
    ser.write(data_to_send.encode('utf-8'))
    return {'status': 'success'}

#Time will be update every 2 minutes
def fetch_current_time_online():
    try:
        response = requests.get('http://worldtimeapi.org/api/timezone/Asia/Karachi')
        data = response.json()
        current_time = datetime.datetime.fromisoformat(data['datetime'])
        formatted_time = current_time.strftime("%y/%m/%d,%H:%M:%S")
        return f"py_time:{formatted_time}+20"
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def send_to_serial_port(serial_data):
    try:
        # ser = serial.Serial('/dev/ttyACM0', 115200)
        ser.write(serial_data.encode())
        # ser.close()
    except serial.SerialException as e:
        print(f"An error occurred while sending data to serial port: {e}")

def update_time():
    current_time = fetch_current_time_online()
    if current_time:
        print(f"Current time in Karachi: {current_time}")
        send_to_serial_port(current_time)
    else:
        print("Failed to fetch current time.")

schedule.every(2).minutes.do(update_time)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6677, debug=True)
    schedule.run_pending()

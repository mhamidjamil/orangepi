# serial_handler.py

import requests
import datetime
import serial

ser = None  # Define serial port globally

def read_serial_data(data):
    if "{hay orange-pi!" in data:
        if "send time" in data or "update time" in data or "send updated time" in data:
            update_time()
        elif "send ip" in data or "update ip" in data or "my ip" in data:
            ip = requests.get('https://api.ipify.org').text
            msg = '{hay ttgo-tcall! here is the ip: ' + ip + '.}'
            print(f"sending : {msg}")
            send_to_serial_port(msg)
        else:
            print(f"unknown keywords in command: {data}")

def read_serial(ser):
    if ser:
        try:
            data = ser.readline().decode('utf-8')
            read_serial_data(data)
            return {'data': data.strip()}  # Strip whitespace from the data
        except UnicodeDecodeError:
            return {'error': 'Error decoding serial data'}
    else:
        return {'error': 'Serial port not accessible'}

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
        ser.write(serial_data.encode())
    except serial.SerialException as e:
        print(f"An error occurred while sending data to serial port: {e}")

def update_time():
    current_time = fetch_current_time_online()
    if current_time:
        print(f"Current time in Karachi: {current_time}")
        send_to_serial_port(current_time)
    else:
        print("Failed to fetch current time.")


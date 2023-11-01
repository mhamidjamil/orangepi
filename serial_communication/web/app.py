
#$ last work 27/Oct/23 [01:58 AM]
## version 1.0.3
## Release Note : started communication with ttgo

from flask import Flask, render_template, request
import serial
import serial.tools.list_ports
import requests
import datetime
import schedule
import threading
import time

app = Flask(__name__)

# Function to get a list of available serial ports
# Modify the get_serial_ports function
def get_serial_ports():
    return [{'port': port.device, 'baud_rate': 115200} for port in serial.tools.list_ports.comports() if port.device.startswith('/dev/tty')]

# Replace with the default serial port
default_serial_port = '/dev/ttyACM0'
ser = None

# Attempt to open the default serial port
try:
    ser = serial.Serial(default_serial_port, 115200)
except serial.SerialException:
    pass  # Handle the exception if the default port is not accessible

@app.route('/')
def index():
    # Get a list of available serial ports with default baud rate
    available_ports = get_serial_ports()

    # Baud rates to be displayed in the dropdown
    baud_rates = [9600, 115200, 230400, 460800, 921600]

    return render_template('index.html', default_port=default_serial_port, available_ports=available_ports, baud_rates=baud_rates)


def read_serial_data(data):
    if "{orange-pi!:" in data:
        if "send time" in data or "update time" in data:
            update_time()
        else:
            print(f"unknown command: {data}")

@app.route('/read_serial')
def read_serial():
    if ser:
        try:
            data = ser.readline().decode('utf-8')
            read_serial_data(data)

            return {'data': data.strip()}  # Strip whitespace from the data
        except UnicodeDecodeError:
            return {'error': 'Error decoding serial data'}
    else:
        return {'error': 'Serial port not accessible'}


@app.route('/send_serial', methods=['POST'])
def send_serial():
    data_to_send = request.form['data']
    ser.write(data_to_send.encode('utf-8'))
    return {'status': 'success'}


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

def update_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    thread = threading.Thread(target=update_schedule)
    thread.start()
    app.run(host='0.0.0.0', port=6677, debug=True)

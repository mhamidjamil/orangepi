"""Main script read project documentation for information"""
# pylint: disable=import-error, no-name-in-module
import time
import sys
import random
import multiprocessing
import threading
from datetime import datetime
from flask import Flask, render_template, request
import serial
import serial.tools.list_ports
import schedule
from routes.serial_handler import (
    set_serial_object, read_serial_data, update_time,
    update_namaz_time, send_ngrok_link, say_to_serial,
    is_ngrok_link_sent, send_message, exception_logger
)
from routes.route import send_auth
from routes.uptime_checker import is_uptime_greater_than_threshold
from routes.communication.ntfy import send_warning

BG_TASK = True
BOOT_MESSAGE_SEND = False
TESTING_ENVIRONMENT = False

app = Flask(__name__)

def get_serial_ports():
    """Return a list of available serial ports."""
    return [{'port': port.device, 'baud_rate': 115200}
            for port in serial.tools.list_ports.comports()
            if port.device.startswith('/dev/tty')]

def update_serial_port():
    """Update the serial port dynamically."""
    try:
        global BG_TASK, ser # pylint: disable=global-statement
        max_port_number = 5  # Maximum port number to try
        port_pattern = '/dev/ttyACM{}'
        print("Trying to connect to port!")
        while True:
            for port_number in range(max_port_number):
                port = port_pattern.format(port_number)
                try:
                    temp_ser = serial.Serial(port, baudrate=115200, timeout=1)
                    ser = temp_ser
                    print(f"Connected to {port}")
                    set_serial_object(ser)
                    BG_TASK = True
                    return temp_ser
                except serial.SerialException:
                    print(f"Port {port} not available. Trying the next one.")

            print(f"No available ports (tried up to {max_port_number}). Retrying in 10 seconds...")
            time.sleep(10)
            update_serial_port()
    except Exception as usp_e: # pylint: disable=broad-except
        exception_logger("update_serial_port", usp_e)
        return None

# Replace with the default serial port
ser = update_serial_port()

@app.route('/')
def index():
    """Render the index page."""
    available_ports = get_serial_ports()
    baud_rates = [9600, 115200, 230400, 460800, 921600]
    return render_template('index.html',
                default_port=ser, available_ports=available_ports, baud_rates=baud_rates)

@app.route('/read_serial')
def read_serial():
    """Read serial data."""
    global BG_TASK  # pylint: disable=global-statement
    try:
        if ser:
            raw_data = ser.readline()
            data = raw_data.decode('utf-8')
            read_serial_data(data)
            return {'data': data.strip()} # Strip whitespace from the data
        return {'error': 'Serial port not accessible'}
    except UnicodeDecodeError as ud:
        exception_logger("read_serial UnicodeDecodeError", ud)
        print(f"Problematic data: {raw_data}")
        return {'result': 'error', 'message': 'UnicodeDecodeError', 'data': raw_data}
    except serial.SerialException as rs:
        BG_TASK = False
        update_serial_port()
        exception_logger("read_serial SerialException", rs)
        return {'result': 'error', 'message': 'Error reading from serial port'}

@app.route('/send_serial', methods=['POST'])
def send_serial():
    """Send data to the serial port."""
    try:
        data_to_send = request.form['data']
        ser.write(data_to_send.encode('utf-8'))
        return {'status': 'success'}
    except Exception as ss: # pylint: disable=broad-except
        exception_logger("send_serial", ss)
        return None

@app.route('/send_auth', methods=['GET'])
def send_auth_route():
    """Send authentication."""
    return send_auth()

@app.route('/inspect', methods=['GET'])
def inspect():
    """Inspect the server."""
    try:
        # Get the 'number' query parameter from the request
        number_param = request.args.get('number', '')

        # Convert the string to an integer
        number = int(number_param)

        # Calculate the sum of digits
        digit_sum = sum(int(digit) for digit in str(abs(number)))

        response_data = {
            'status': 'success',
            'message': f'Sum of digits: {digit_sum}'
        }
        return response_data
    except ValueError as e:
        response_data = {
            'status': 'error',
            'message': f'Invalid number parameter: {e}'
        }
        return response_data

if BG_TASK:
    schedule.every(2).minutes.do(update_time)
    schedule.every(5).minutes.do(update_namaz_time)

def update_schedule():
    """Update the schedule."""
    while True:
        schedule.run_pending()
        time.sleep(10)

def one_time_task():
    """Execute one-time tasks."""
    try:
        global BOOT_MESSAGE_SEND # pylint: disable=global-statement
        if not is_ngrok_link_sent():
            time.sleep(10)
            if not TESTING_ENVIRONMENT:
                if not BOOT_MESSAGE_SEND:
                    send_message("Script just started boot code: " +
                        str(random.randint(10000, 99999)))
                    BOOT_MESSAGE_SEND = True
                time.sleep(5)
            say_to_serial("sms sending?")
            time.sleep(15)
            send_ngrok_link()
    except Exception as ott: # pylint: disable=broad-except
        exception_logger("one_time_task", ott)

if __name__ == '__main__':
    try:
        # lsof -i :6677 #to know which process is using this port
        current_time = datetime.now()
        formatted_time = current_time.strftime("%H:%M:%S")
        print(f"Main script last run time: {formatted_time}")
        send_warning(f"Main script started at: {formatted_time}")
        script_rebooted = is_uptime_greater_than_threshold(10)
        print(f"State of system uptime {script_rebooted}")
        if len(sys.argv) > 1:
            # If there are no command-line arguments, assume it's called as a service
            print("\n-----------> Running as a service <-----------\n")
            if not script_rebooted:
                print("\n\tHave to wait untill system stabilize")
                send_warning("have to wait untill system stabilize")
                time.sleep(600)
            else:
                print("\n\tSkipping delay as system is stable")
        else:
            # If there are command-line arguments, assume it's called from the terminal
            time.sleep(3)
            print("\n-----------> Running from terminal <-----------\n")
            TESTING_ENVIRONMENT = True

        current_process_id = multiprocessing.current_process().pid
        print(f"!!----------> Process ID: {current_process_id} - Executing my_function")

        thread = threading.Thread(target=update_schedule)
        thread2 = threading.Thread(target=one_time_task)
        send_warning("app started")
        thread.start()
        thread2.start()
        app.run(host='0.0.0.0', port=6677, debug=False) #don't move above thread work

    except Exception as m: # pylint: disable=broad-except
        print(f"Exception in main: {m}")

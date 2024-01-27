"""Main script read project documentation for information"""
import time
import sys
import multiprocessing
import threading
from flask import Flask, render_template, request
import serial
import serial.tools.list_ports
import schedule
from routes.serial_handler import (
    set_serial_object, read_serial_data, update_time,
    update_namaz_time, send_ngrok_link, say_to_serial,
    is_ngrok_link_sent, send_message, fetch_current_time_online,
    exception_logger
)
from routes.routes import send_auth

BG_TASK = True
BOOT_MESSAGE_SEND = False

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
    global BG_TASK # pylint: disable=global-statement
    try:
        if ser:
            data = ser.readline().decode('utf-8')
            read_serial_data(data)
            return {'data': data.strip()}  # Strip whitespace from the data
        return {'error': 'Serial port not accessible'}
    except serial.SerialException as rs:
        BG_TASK = False
        update_serial_port()
        exception_logger("read_serial", rs)
        return {'error': 'Error reading from serial port'}

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
            if not BOOT_MESSAGE_SEND:
                send_message("Orange Pi just boot-up time stamp: " + fetch_current_time_online())
                BOOT_MESSAGE_SEND = True
            time.sleep(5)
            say_to_serial("sms sending?")
            time.sleep(5)
            send_ngrok_link()
    except Exception as ott: # pylint: disable=broad-except
        exception_logger("one_time_task", ott)

if __name__ == '__main__':
    try:

        if len(sys.argv) > 1:
            print("\n-----------> Running as a service <-----------\n")
            time.sleep(600)
        else:
            time.sleep(3)
            print("\n-----------> Running from terminal <-----------\n")

        current_process_id = multiprocessing.current_process().pid
        print(f"!!----------> Process ID: {current_process_id} - Executing my_function")

        app.run(host='0.0.0.0', port=6677)
        thread = threading.Thread(target=update_schedule)
        thread2 = threading.Thread(target=one_time_task)
        thread.start()
        thread2.start()

    except Exception as m: # pylint: disable=broad-except
        print(f"Exception in main: {m}")

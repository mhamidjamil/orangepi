

#$ last work 27/Jan/24 [03:00 AM]
## version 2.0.6
## Release Note : Added pylint action

import time
import sys
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

# Function to get a list of available serial ports
# Modify the get_serial_ports function


def get_serial_ports():
    return [{'port': port.device, 'baud_rate': 115200}
            for port in serial.tools.list_ports.comports()
                if port.device.startswith('/dev/tty')]

# Function to update the serial port dynamically


def update_serial_port():
    try:
        global BG_TASK, ser
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

            print(
                f"No available ports (tried up to {max_port_number}). Retrying in 10 seconds...")
            time.sleep(10)
            update_serial_port()  # TODO: this effect execution flow
    except Exception as e:
        exception_logger("update_serial_port", e)


# Replace with the default serial port
ser = update_serial_port()


@app.route('/')
def index():
    # Get a list of available serial ports with default baud rate
    available_ports = get_serial_ports()

    # Baud rates to be displayed in the dropdown
    baud_rates = [9600, 115200, 230400, 460800, 921600]

    return render_template('index.html', default_port=ser, available_ports=available_ports, baud_rates=baud_rates)


@app.route('/read_serial')
def read_serial():
    global BG_TASK
    try:
        if ser:
            try:
                data = ser.readline().decode('utf-8')
                read_serial_data(data)

                return {'data': data.strip()}  # Strip whitespace from the data
            except UnicodeDecodeError:
                return {'error': 'Error decoding serial data'}
        else:
            return {'error': 'Serial port not accessible'}
    except serial.SerialException as e:
        BG_TASK = False
        update_serial_port()
        exception_logger("read_serial", e)
        return {'error': 'Error reading from serial port'}


@app.route('/send_serial', methods=['POST'])
def send_serial():
    try:
        data_to_send = request.form['data']
        ser.write(data_to_send.encode('utf-8'))
        return {'status': 'success'}
    except Exception as e:
        exception_logger("send_serial", e)


@app.route('/send_auth', methods=['GET'])
def send_auth_route():
    return send_auth()


if BG_TASK:
    schedule.every(2).minutes.do(update_time)
    schedule.every(5).minutes.do(update_namaz_time)  # TODO: implement array


def update_schedule():
    while True:
        schedule.run_pending()  # run background task after specified delay
        time.sleep(10)


def one_time_task():
    try:
        global BOOT_MESSAGE_SEND
        # Delay the execution of send_ngrok_link() by 5 minutes

        # Check if send_ngrok_link() has not been called yet
        if not is_ngrok_link_sent():
            time.sleep(10)
            if not BOOT_MESSAGE_SEND:
                send_message("Orange Pi just boot-up time stamp: " +
                             fetch_current_time_online())
                BOOT_MESSAGE_SEND = True # pylint: disable=W0603
            time.sleep(5)
            say_to_serial("sms sending?")
            time.sleep(5)
            send_ngrok_link()
    except Exception as e:
        exception_logger("one_time_task", e)


if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            # If there are no command-line arguments, assume it's called as a service
            print("\n-----------> Running as a service <-----------\n")
            time.sleep(600)  # wait for some time until routers power on
        else:
            # If there are command-line arguments, assume it's called from the terminal
            time.sleep(3)
            print("\n-----------> Running from terminal <-----------\n")
        thread = threading.Thread(target=update_schedule)
        thread2 = threading.Thread(target=one_time_task)
        thread.start()
        thread2.start()

        # Run the Flask app
        app.run(host='0.0.0.0', port=6677, debug=True)
    except Exception as e:
        print(f"Exception in main: {e}")

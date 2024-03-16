"""Main script read project documentation for information"""
# pylint: disable=import-error, no-name-in-module
import time
import sys
import random
import multiprocessing
import threading
from flask import jsonify, Flask, render_template, request
import serial
import serial.tools.list_ports
import schedule
from routes.serial_handler import (
    set_serial_object, read_serial_data, update_time,
    update_namaz_time, send_ngrok_link, say_to_serial,
    is_ngrok_link_sent, send_message, exception_logger,
    sync_company_numbers, fetch_current_time_online
)
from routes.route import send_auth
from routes.uptime_checker import is_uptime_greater_than_threshold
from routes.communication.ntfy import send_warning, send_info
from routes.watcher import initialize_port, blink, update_serial_port

BG_TASK = True
BOOT_MESSAGE_SEND = False
TESTING_ENVIRONMENT = False
TTGO_TCALL_PORT = "/dev/ttyACM"
COMMUNICATION_PORT = None

app = Flask(__name__)

def get_serial_ports():
    """Return a list of available serial ports."""
    return [{'port': port.device, 'baud_rate': 115200}
            for port in serial.tools.list_ports.comports()
            if port.device.startswith('/dev/tty')]

# Replace with the default serial port
ser = update_serial_port(TTGO_TCALL_PORT)
set_serial_object(ser)
if COMMUNICATION_PORT is None:
    COMMUNICATION_PORT = ser
# ser = serial.Serial('/dev/ttyUSB0', 115200)

@app.route('/')
def index():
    """Render the index page."""
    available_ports = get_serial_ports()

    if COMMUNICATION_PORT:
        print(f"\n\n\t\t sending to default index.html: {COMMUNICATION_PORT}")
        return render_template('index.html',
                               default_port=COMMUNICATION_PORT,
                               available_ports=available_ports)
    print("\n\n\t\t !!!___Sending default to index.html___!!!")
    return render_template('index.html',
                            default_port=ser,
                            available_ports=available_ports)

@app.route('/update_port', methods=['POST'])
def update_port():
    """To update port dynamically from the web page"""
    try:
        selected_port = request.get_json().get('port')
        if selected_port is not None:
            print("Trying to change to: " + selected_port)
            global ser, COMMUNICATION_PORT # pylint: disable=global-statement
            ser = serial.Serial(selected_port, 115200)
            COMMUNICATION_PORT = ser
            print("\n\n\t\t### Port updated successfully ###")
            return jsonify({'status': 'success', 'message': 'Port updated successfully'})

        print("No port provided in the request.")
        return jsonify({'status': 'error', 'message': 'No port provided'})
    except Exception as e: # pylint: disable=broad-except
        print("Error updating port:", e)
        return jsonify({'status': 'error', 'message': 'Error updating port'})


@app.route('/read_serial')
def read_serial():
    """Read serial data."""
    global BG_TASK  # pylint: disable=global-statement
    try:
        if ser:
            raw_data = ser.readline()
            data = raw_data.decode('utf-8')  # Decode bytes to string
            read_serial_data(data)
            return jsonify({'data': data.strip()})  # Return JSON response
        return jsonify({'error': 'Serial port not accessible'})
    except UnicodeDecodeError as ud:
        exception_logger("read_serial UnicodeDecodeError", ud)
        print(f"Problematic data: {raw_data}")
        return jsonify({'result': 'error', 'message': 'UnicodeDecodeError',
             'data': raw_data.decode('utf-8')})
    except serial.SerialException as rs:
        BG_TASK = False
        update_serial_port(TTGO_TCALL_PORT)
        BG_TASK = True
        exception_logger("read_serial SerialException", rs)
        return jsonify({'result': 'error', 'message': 'Error reading from serial port'})

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
    schedule.every(30).minutes.do(sync_company_numbers)

def update_schedule():
    """Update the schedule."""
    while True:
        schedule.run_pending()
        time.sleep(10)

def one_time_task():
    """Execute one-time tasks."""
    try:
        global BOOT_MESSAGE_SEND # pylint: disable=global-statement
        update_time()
        update_namaz_time()
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

def initialize_port_in_thread():
    """This will initialize Watcher in separate thread"""
    t1 = threading.Thread(target=initialize_port)
    t1.start()
    while t1.is_alive():
        time.sleep(1)

    t1 = threading.Thread(target=blink, args=(5,100))
    t1.start()
    while t1.is_alive():
        time.sleep(1)

    # t.join()  # Wait for the thread to finish

if __name__ == '__main__':
    try:
        # lsof -i :6677 #to know which process is using this port
        initialize_port_in_thread()
        print(f"Main script last run time: {fetch_current_time_online()}")
        script_rebooted = is_uptime_greater_than_threshold(10)
        send_info(f"\n\nMain script started at: {fetch_current_time_online()} and "
                 f"{'run manually' if script_rebooted else 'run by service'}")

        if len(sys.argv) > 1:
            # If there are no command-line arguments, assume it's called as a service
            print("\n-----------> Running as a service <-----------\n")
            if not script_rebooted:
                print("\n\tHave to wait until system stabilize")
                send_warning("have to wait until system stabilize")
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
        send_info("app started")
        thread.start()
        thread2.start()
        app.run(host='0.0.0.0', port=6677, debug=False) #don't move above thread work

    except Exception as m: # pylint: disable=broad-except
        print(f"Exception in main: {m}")
